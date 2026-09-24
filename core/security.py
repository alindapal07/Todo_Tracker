from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from pwdlib import PasswordHash
from core.config import settings


password_hasher = PasswordHash.recommended()




def hash_password(password: str) -> str:
    """Hash a plain text password using argon2id."""
    return password_hasher.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored hash."""
    try:
        return password_hasher.verify(plain_password, hashed_password)
    except Exception:
        return False




def create_access_token(
    user_id: str | None = None,
    username: str | None = None,
    data: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    
    payload = data.copy() if data else {}
    if user_id is not None:
        payload["sub"] = str(user_id)
    if username is not None:
        payload["username"] = username

    if expires_delta is not None:
        expires_at = datetime.now(timezone.utc) + expires_delta
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload["exp"] = expires_at

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )






def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
