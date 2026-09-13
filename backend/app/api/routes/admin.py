from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.entities import AuditEvent, Conversation, Document, Employee, Role, User
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/metrics")
async def metrics(
    _: CurrentUser = Depends(require_roles(Role.HR, Role.ADMIN)), db: AsyncSession = Depends(get_db)
) -> dict:
    async def count(model) -> int:
        return int(await db.scalar(select(func.count()).select_from(model)) or 0)
    return {
        "users": await count(User), "employees": await count(Employee),
        "documents": await count(Document), "conversations": await count(Conversation),
    }


@router.get("/audit-events")
async def audit_events(
    _: CurrentUser = Depends(require_roles(Role.ADMIN)), db: AsyncSession = Depends(get_db)
) -> list[dict]:
    rows = (await db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200))).all()
    return [
        {"id": row.id, "actor_user_id": row.actor_user_id, "action": row.action,
         "resource_type": row.resource_type, "resource_id": row.resource_id,
         "details": row.details, "created_at": row.created_at}
        for row in rows
    ]

