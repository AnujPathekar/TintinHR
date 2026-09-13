import asyncio
from uuid import UUID

from celery import Celery

from app.core.config import settings
from app.services.ingestion import index_document

celery = Celery("tintinhr", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(task_track_started=True, task_serializer="json", result_serializer="json")


@celery.task(name="index_document", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def index_document_task(document_id: str) -> None:
    asyncio.run(index_document(UUID(document_id)))

