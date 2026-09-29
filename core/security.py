from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any
import uuid
import jwt
from pwdlib import PasswordHash
from core.config import settings

password_hasher = PasswordHash.recommended()


# =============================================================================
# Password Utilities
# =============================================================================

def hash_password(password: str) -> str:
    # hashes the user password safely using argon2
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # checks if the plain password matches the stored hash
    try:
        return password_hasher.verify(plain_password, hashed_password)
    except Exception:
        return False


# =============================================================================
# Access Token (JWT) Utilities
# =============================================================================

def create_access_token(
    user_id: uuid.UUID | str | None = None,
    username: str | None = None,
    data: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    # creates a signed jwt access token
    payload = data.copy() if data else {}
    if user_id is not None:
        payload["sub"] = str(user_id)
    if username is not None:
        payload["username"] = username

    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expires_at = now + expires_delta
    else:
        expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 15)
        expires_at = now + timedelta(minutes=expire_minutes)

    payload["iat"] = now
    payload["jti"] = str(uuid.uuid4())
    payload["exp"] = expires_at

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    # decodes and checks the jwt signature and expiry
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# =============================================================================
# Refresh Token Utilities
# =============================================================================

def create_refresh_token() -> str:
    # generates a random secure string for refresh token
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    # hashes the raw token with sha256 before storing in db
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()