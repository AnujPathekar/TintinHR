from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    conversation_id: UUID | None = None


class Citation(BaseModel):
    index: int
    chunk_id: UUID
    document_id: UUID
    title: str
    filename: str
    page_number: int | None
    quote: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    citations: list[Citation]
    confidence: float
    route: str
    latency_ms: int


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    citations: list[dict]
    created_at: datetime


class ConversationOut(BaseModel):
    id: UUID
    title: str
    updated_at: datetime

