import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


# refresh token table to store hashed tokens for user sessions
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # unique id for each token entry
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # links to the user table using string uuid
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("user-table.id", ondelete="CASCADE"), nullable=False
    )

    # sha-256 hash of the refresh token (never store raw token in db)
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # kept for db schema compatibility
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, default=uuid.uuid4, nullable=False
    )

    # whether this token has been used or cancelled
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # expiration timestamp in utc
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    # creation timestamp in utc
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # optional client ip and user-agent for tracking
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # points to new token when rotated
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    __table_args__ = (
        Index("idx_active_tokens", "token_hash", "is_revoked", "expires_at"),
    )
