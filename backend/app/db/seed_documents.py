import asyncio
import hashlib
import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import (
    Document,
    DocumentStatus,
    DocumentVersion,
    Role,
    User,
    Visibility,
)
from app.services.ingestion import index_document


def source_directory() -> Path:
    mounted = Path("/sample_docs")
    return mounted if mounted.exists() else Path(__file__).resolve().parents[3] / "sample_docs"


async def seed_documents() -> None:
    source_dir = source_directory()
    if not source_dir.exists():
        raise RuntimeError(f"Sample document directory not found: {source_dir}")
    new_ids = []
    async with SessionLocal() as db:
        uploader = await db.scalar(select(User).where(User.role == Role.HR))
        if not uploader:
            raise RuntimeError("Run `python -m app.db.seed` first")
        for source in sorted(source_dir.iterdir()):
            if not source.is_file():
                continue
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if await db.scalar(select(Document.id).where(Document.sha256 == digest)):
                continue
            document_id = uuid4()
            target_dir = Path("uploads") / str(document_id)
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"v1-{source.name}"
            shutil.copy2(source, target)
            document = Document(
                id=document_id,
                title=source.stem.replace("_", " "),
                filename=source.name,
                mime_type=mimetypes.guess_type(source.name)[0] or "text/plain",
                sha256=digest,
                visibility=Visibility.EMPLOYEE,
                status=DocumentStatus.PENDING,
                current_version=1,
                corpus_version=1,
                uploaded_by=uploader.id,
            )
            db.add(document)
            db.add(
                DocumentVersion(
                    id=uuid4(),
                    document_id=document_id,
                    version=1,
                    storage_path=str(target),
                    sha256=digest,
                    size_bytes=source.stat().st_size,
                )
            )
            new_ids.append(document_id)
        await db.commit()
    for document_id in new_ids:
        await index_document(document_id)
    print(f"Indexed {len(new_ids)} sample documents.")


if __name__ == "__main__":
    asyncio.run(seed_documents())
