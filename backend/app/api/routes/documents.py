import hashlib
import re
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import Document, DocumentStatus, DocumentVersion, Role, Visibility
from app.rag.access import build_access_scope
from app.schemas.auth import CurrentUser
from app.services.audit import record_audit
from app.services.rate_limit import enforce_rate_limit
from app.workers.celery_app import index_document_task

router = APIRouter(prefix="/documents", tags=["Documents"])
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)
    return cleaned[:200] or "document"


def serialize(document: Document) -> dict:
    return {
        "id": document.id, "title": document.title, "filename": document.filename,
        "visibility": document.visibility.value, "department_id": document.department_id,
        "status": document.status.value, "current_version": document.current_version,
        "failure_reason": document.failure_reason, "created_at": document.created_at,
    }


@router.get("")
async def list_documents(
    user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[dict]:
    scope = build_access_scope(user)
    query = select(Document).where(
        Document.visibility.in_(scope.visibilities),
        (Document.department_id.is_(None) | (Document.department_id == scope.department_id)),
        Document.status != DocumentStatus.ARCHIVED,
    ).order_by(Document.updated_at.desc())
    return [serialize(item) for item in (await db.scalars(query)).all()]


@router.post("", status_code=202)
async def upload_document(
    title: str = Form(...), visibility: Visibility = Form(Visibility.EMPLOYEE),
    department_id: UUID | None = Form(None), valid_from: date | None = Form(None),
    valid_until: date | None = Form(None), file: UploadFile = File(...),
    user: CurrentUser = Depends(require_roles(Role.HR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await enforce_rate_limit(f"upload:{user.id}", 20, 3600)
    filename = safe_name(file.filename or "document")
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, detail="Supported formats: PDF, DOCX, TXT and CSV")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, detail=f"File exceeds {settings.max_upload_mb} MB")
    digest = hashlib.sha256(content).hexdigest()
    duplicate = await db.scalar(
        select(Document).where(Document.sha256 == digest, Document.status != DocumentStatus.ARCHIVED)
    )
    if duplicate:
        raise HTTPException(409, detail="This exact document is already uploaded")
    document_id = uuid4()
    storage_dir = Path("uploads") / str(document_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"v1-{filename}"
    storage_path.write_bytes(content)
    document = Document(
        id=document_id, title=title.strip(), filename=filename,
        mime_type=file.content_type or "application/octet-stream", sha256=digest,
        visibility=visibility, department_id=department_id, status=DocumentStatus.PENDING,
        current_version=1, corpus_version=1, valid_from=valid_from, valid_until=valid_until,
        uploaded_by=user.id,
    )
    db.add(document)
    db.add(
        DocumentVersion(
            id=uuid4(), document_id=document.id, version=1, storage_path=str(storage_path),
            sha256=digest, size_bytes=len(content),
        )
    )
    await record_audit(db, "document.upload", "document", user.id, str(document.id), {"title": title})
    await db.commit()
    index_document_task.delay(str(document.id))
    return serialize(document)


@router.patch("/{document_id}")
async def update_document(
    document_id: UUID, title: str | None = None, visibility: Visibility | None = None,
    department_id: UUID | None = None,
    user: CurrentUser = Depends(require_roles(Role.HR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    document = await db.get(Document, document_id)
    if not document or document.status == DocumentStatus.ARCHIVED:
        raise HTTPException(404, detail="Document not found")
    if title is not None:
        document.title = title.strip()
    if visibility is not None:
        document.visibility = visibility
    document.department_id = department_id
    document.corpus_version += 1
    await record_audit(db, "document.update", "document", user.id, str(document.id))
    await db.commit()
    return serialize(document)


@router.put("/{document_id}/content", status_code=202)
async def replace_document_content(
    document_id: UUID,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_roles(Role.HR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    document = await db.get(Document, document_id)
    if not document or document.status == DocumentStatus.ARCHIVED:
        raise HTTPException(404, detail="Document not found")
    filename = safe_name(file.filename or document.filename)
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, detail="Supported formats: PDF, DOCX, TXT and CSV")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, detail=f"File exceeds {settings.max_upload_mb} MB")
    digest = hashlib.sha256(content).hexdigest()
    if digest == document.sha256:
        raise HTTPException(409, detail="The replacement is identical to the current version")
    next_version = document.current_version + 1
    storage_dir = Path("uploads") / str(document.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"v{next_version}-{filename}"
    storage_path.write_bytes(content)
    db.add(
        DocumentVersion(
            id=uuid4(), document_id=document.id, version=next_version,
            storage_path=str(storage_path), sha256=digest, size_bytes=len(content),
        )
    )
    document.current_version = next_version
    document.filename = filename
    document.mime_type = file.content_type or "application/octet-stream"
    document.sha256 = digest
    document.status = DocumentStatus.PENDING
    document.failure_reason = None
    await record_audit(
        db, "document.replace", "document", user.id, str(document.id), {"version": next_version}
    )
    await db.commit()
    index_document_task.delay(str(document.id))
    return serialize(document)


@router.delete("/{document_id}", status_code=204)
async def archive_document(
    document_id: UUID, user: CurrentUser = Depends(require_roles(Role.HR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(404, detail="Document not found")
    document.status = DocumentStatus.ARCHIVED
    document.corpus_version += 1
    await record_audit(db, "document.archive", "document", user.id, str(document.id))
    await db.commit()
