import uuid
from datetime import datetime

from db.base import Base
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "user-table"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    @property
    def username(self) -> str:
        return self.name

    @username.setter
    def username(self, value: str) -> None:
        self.name = value

    @property
    def password_hash(self) -> str:
        return self.password

    @password_hash.setter
    def password_hash(self, value: str) -> None:
        self.password = value

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )