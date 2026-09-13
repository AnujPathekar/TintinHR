from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: UUID
    title: str
    description: str | None
    filename: str
    mime_type: str
    visibility: str
    department_id: UUID | None
    status: str
    current_version: int
    failure_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    visibility: str | None = None
    department_id: UUID | None = None
    valid_from: date | None = None
    valid_until: date | None = None

