from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, create_token, decode_token, verify_password
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.services.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    await enforce_rate_limit(f"login:{payload.email.lower()}", 10, 300)
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, detail="Invalid email or password")
    return TokenPair(
        access_token=create_token(user.id, user.role.value, TokenType.ACCESS),
        refresh_token=create_token(user.id, user.role.value, TokenType.REFRESH),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, TokenType.REFRESH)
    except ValueError as exc:
        raise HTTPException(401, detail=str(exc)) from exc
    user = await db.get(User, claims.sub)
    if not user or not user.is_active or user.role.value != claims.role:
        raise HTTPException(401, detail="Account is unavailable or permissions changed")
    return TokenPair(
        access_token=create_token(user.id, user.role.value, TokenType.ACCESS),
        refresh_token=create_token(user.id, user.role.value, TokenType.REFRESH),
    )

