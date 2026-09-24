import uuid
from datetime import date

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from schemas.todo_schema import TodoCategory, TodoPriority, TodoStatus


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("user-table.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[TodoStatus] = mapped_column(String, default=TodoStatus.pending)
    priority: Mapped[TodoPriority] = mapped_column(String, default=TodoPriority.medium)
    category: Mapped[TodoCategory] = mapped_column(String, default=TodoCategory.personal)

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)