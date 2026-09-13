from uuid import uuid4

import pytest

from app.core.security import TokenType, create_token, decode_token, hash_password, verify_password


def test_password_hash_and_token_type() -> None:
    hashed = hash_password("StrongPassword123!")
    assert verify_password("StrongPassword123!", hashed)
    assert not verify_password("wrong-password", hashed)
    user_id = uuid4()
    token = create_token(user_id, "employee", TokenType.ACCESS)
    assert decode_token(token, TokenType.ACCESS).sub == user_id
    with pytest.raises(ValueError):
        decode_token(token, TokenType.REFRESH)

