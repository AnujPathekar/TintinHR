from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDMixin


class Role(StrEnum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR = "hr"
    ADMIN = "admin"


class Visibility(StrEnum):
    PUBLIC = "public"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR = "hr"
    ADMIN = "admin"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    ACTIVE = "active"
    FAILED = "failed"
    ARCHIVED = "archived"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), default=Role.EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    authz_version: Mapped[int] = mapped_column(Integer, default=1)
    employee: Mapped[Employee | None] = relationship(back_populates="user", uselist=False)


class Department(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    name: Mapped[str] = mapped_column(String(120), unique=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)


class Employee(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employees"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    employee_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    department_id: Mapped[UUID | None] = mapped_column(ForeignKey("departments.id"))
    manager_id: Mapped[UUID | None] = mapped_column(ForeignKey("employees.id"))
    joining_date: Mapped[date] = mapped_column(Date)
    job_title: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(120), default="Bengaluru")
    user: Mapped[User] = relationship(back_populates="employee")
    department: Mapped[Department | None] = relationship()


class LeaveBalance(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "leave_balances"
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    leave_type: Mapped[str] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer)
    allocated: Mapped[float] = mapped_column(Float)
    used: Mapped[float] = mapped_column(Float, default=0)
    pending: Mapped[float] = mapped_column(Float, default=0)
    __table_args__ = (Index("uq_leave_employee_type_year", "employee_id", "leave_type", "year", unique=True),)


class LeaveRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "leave_requests"
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    leave_type: Mapped[str] = mapped_column(String(80))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    days: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30))


class Holiday(UUIDMixin, Base):
    __tablename__ = "holidays"
    name: Mapped[str] = mapped_column(String(150))
    holiday_date: Mapped[date] = mapped_column(Date, index=True)
    location: Mapped[str | None] = mapped_column(String(120))
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(300))
    mime_type: Mapped[str] = mapped_column(String(120))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    visibility: Mapped[Visibility] = mapped_column(Enum(Visibility, name="document_visibility"))
    department_id: Mapped[UUID | None] = mapped_column(ForeignKey("departments.id"), index=True)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus, name="document_status"))
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    corpus_version: Mapped[int] = mapped_column(Integer, default=1)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    versions: Mapped[list[DocumentVersion]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_versions"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    document: Mapped[Document] = relationship(back_populates="versions")
    __table_args__ = (Index("uq_document_version", "document_id", "version", unique=True),)


class DocumentChunk(UUIDMixin, Base):
    __tablename__ = "document_chunks"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(250))
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    search_vector: Mapped[Any] = mapped_column(TSVECTOR, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimension))
    __table_args__ = (
        Index("ix_chunks_fts", "search_vector", postgresql_using="gin"),
        Index("ix_chunks_embedding", "embedding", postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"}),
    )


class Conversation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversations"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="New conversation")


class Message(UUIDMixin, Base):
    __tablename__ = "messages"
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name="message_role"))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    trace: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditEvent(UUIDMixin, Base):
    __tablename__ = "audit_events"
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    resource_type: Mapped[str] = mapped_column(String(120))
    resource_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

