from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import TokenType, decode_token
from app.db.session import get_db
from app.models.entities import Role, User
from app.schemas.auth import CurrentUser

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        claims = decode_token(credentials.credentials, TokenType.ACCESS)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    user = await db.scalar(select(User).options(selectinload(User.employee)).where(User.id == claims.sub))
    if not user or not user.is_active or user.role.value != claims.role:
        raise HTTPException(status_code=401, detail="Account is unavailable or permissions changed")
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        department_id=user.employee.department_id if user.employee else None,
        authz_version=user.authz_version,
    )


def require_roles(*roles: Role) -> Callable:
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in {role.value for role in roles}:
            raise HTTPException(status_code=403, detail="Insufficient permission")
        return user

    return checker

