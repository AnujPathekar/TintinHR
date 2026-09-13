from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID

from jose import JWTError, jwt
from pwdlib import PasswordHash
from pydantic import BaseModel

from app.core.config import settings

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenClaims(BaseModel):
    sub: UUID
    role: str
    token_type: TokenType
    exp: datetime


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_token(user_id: UUID, role: str, token_type: TokenType) -> str:
    lifetime = (
        timedelta(minutes=settings.access_token_expire_minutes)
        if token_type == TokenType.ACCESS
        else timedelta(days=settings.refresh_token_expire_days)
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "token_type": token_type.value,
        "exp": datetime.now(UTC) + lifetime,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, required_type: TokenType) -> TokenClaims:
    try:
        claims = TokenClaims.model_validate(jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM]))
    except (JWTError, ValueError) as exc:
        raise ValueError("Invalid or expired token") from exc
    if claims.token_type != required_type:
        raise ValueError("Incorrect token type")
    return claims

