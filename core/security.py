from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any
import uuid
import jwt
from pwdlib import PasswordHash
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.refreshToken_model import RefreshToken  
from models.user_model import User                 

password_hasher = PasswordHash.recommended()


# =============================================================================
# Password Utilities
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a plain text password using argon2id."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored hash."""
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
    """Generate a signed JWT access token."""
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
    """Decode and validate a JWT access token."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# =============================================================================
# Refresh Token Utilities & DB Operations
# =============================================================================

def hash_refresh_token(raw_token: str) -> str:
    """Compute SHA-256 hash of raw token for storage and lookups."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def create_refresh_token(
    db: AsyncSession,
    user_id: str | uuid.UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
    family_id: uuid.UUID | None = None,
    expire_days: int | None = None,
) -> tuple[str, RefreshToken]:
    """
    Generates a secure random refresh token, stores its hash in the database,
    and returns both the raw token and the ORM record.
    """
    if expire_days is None:
        expire_days = getattr(settings, "REFRESH_TOKEN_EXPIRY_TIME", 15)

    raw_token = secrets.token_urlsafe(64)
    token_hash = hash_refresh_token(raw_token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expire_days)

    token_record = RefreshToken(
        id=uuid.uuid4(),
        user_id=str(user_id),
        token_hash=token_hash,
        family_id=family_id or uuid.uuid4(),
        expires_at=expires_at,
        created_at=now,
        is_revoked=False,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(token_record)
    await db.commit()
    await db.refresh(token_record)

    return raw_token, token_record


async def refresh_session(
    db: AsyncSession,
    raw_refresh_token: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[dict[str, str], str]:
    """
    Validates the refresh token, performs rotation, checks for token reuse attacks,
    and returns a new access token and rotated refresh token.
    """
    incoming_hash = hash_refresh_token(raw_refresh_token)

    statement = select(RefreshToken).where(RefreshToken.token_hash == incoming_hash)
    result = await db.execute(statement)
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise ValueError("Invalid refresh token")

    if token_record.is_revoked:
        revoke_family_query = (
            update(RefreshToken)
            .where(RefreshToken.family_id == token_record.family_id)
            .values(is_revoked=True)
        )
        await db.execute(revoke_family_query)
        await db.commit()
        raise ValueError("Compromised session detected. Please log in again.")

    now = datetime.now(timezone.utc)
    if token_record.expires_at <= now:
        token_record.is_revoked = True
        await db.commit()
        raise ValueError("Refresh token expired")

    user_query = select(User).where(User.id == str(token_record.user_id))
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        token_record.is_revoked = True
        await db.commit()
        raise ValueError("User account is inactive or deleted")

    new_raw_refresh_token, new_token_record = await create_refresh_token(
        db=db,
        user_id=user.id,
        family_id=token_record.family_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    token_record.is_revoked = True
    token_record.replaced_by = new_token_record.id

    new_access_token = create_access_token(
        user_id=user.id,
        username=user.username,
    )

    await db.commit()

    token_payload = {
        "access_token": new_access_token,
        "refresh_token": new_raw_refresh_token,
        "token_type": "bearer",
    }
    return token_payload, new_raw_refresh_token


async def revoke_refresh_token(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revokes a refresh token on logout."""
    incoming_hash = hash_refresh_token(raw_refresh_token)
    statement = (
        update(RefreshToken)
        .where(RefreshToken.token_hash == incoming_hash)
        .values(is_revoked=True)
    )
    await db.execute(statement)
    await db.commit()