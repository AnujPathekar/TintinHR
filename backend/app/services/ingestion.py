from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.entities import Document, DocumentChunk, DocumentStatus, DocumentVersion
from app.rag.chunking import chunk_pages
from app.rag.embeddings import get_embedding_service
from app.services.document_parser import parse_document


async def index_document(document_id: UUID) -> None:
    async with SessionLocal() as db:
        document = await db.get(Document, document_id)
        if not document:
            return
        document.status = DocumentStatus.PROCESSING
        await db.commit()
        try:
            version = await db.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.version == document.current_version,
                )
            )
            if not version:
                raise ValueError("Document version not found")
            pages = parse_document(version.storage_path, document.mime_type)
            chunks = chunk_pages(pages)
            if not chunks:
                raise ValueError("No readable text was extracted")
            vectors = await get_embedding_service().embed_documents([chunk.text for chunk in chunks])
            await db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id == document.id,
                    DocumentChunk.version == document.current_version,
                )
            )
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
                db.add(
                    DocumentChunk(
                        id=uuid4(), document_id=document.id, version=document.current_version,
                        chunk_index=index, page_number=chunk.page_number, section=chunk.section,
                        content=chunk.text, token_count=chunk.token_count,
                        metadata_json={"ingested_at": datetime.now(UTC).isoformat()}, embedding=vector,
                    )
                )
            document.status = DocumentStatus.ACTIVE
            document.failure_reason = None
            document.corpus_version += 1
            await db.commit()
        except Exception as exc:
            await db.rollback()
            document = await db.get(Document, document_id)
            if document:
                document.status = DocumentStatus.FAILED
                document.failure_reason = str(exc)[:1000]
                await db.commit()
            raise

