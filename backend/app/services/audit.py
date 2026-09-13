from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditEvent


async def record_audit(
    db: AsyncSession,
    action: str,
    resource_type: str,
    actor_user_id: UUID | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            created_at=datetime.now(UTC),
        )
    )

