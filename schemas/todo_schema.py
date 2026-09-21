from pydantic import BaseModel, Field
from enum import Enum
from datetime import date


class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class TodoPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TodoCategory(str, Enum):
    work = "work"
    personal = "personal"
    study = "study"
    health = "health"
    finance = "finance"
    shopping = "shopping"
    events = "events"

class TodoIn(BaseModel):
    title: str = Field(
        ...,
        min_length=8,
        max_length=50
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=200
    )
    status: TodoStatus = TodoStatus.pending
    priority: TodoPriority = TodoPriority.medium
    due_date: date | None = None
    category: TodoCategory = TodoCategory.personal
    tags: list[str] = Field(
        default_factory=list
    )
    is_favorite: bool = False
    estimated_minutes: int | None = Field(
        default=None,
        gt=0
    )

class TodoUpdate(BaseModel):

    title: str | None = Field(
        default=None,
        min_length=8,
        max_length=50
    )
    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=200
    )
    status: TodoStatus | None = None
    priority: TodoPriority | None = None
    due_date: date | None = None
    category: TodoCategory | None = None
    tags: list[str] | None = None
    is_favorite: bool | None = None
    estimated_minutes: int | None = Field(
        default=None,
        gt=0
    )

class TodoResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: TodoStatus
    priority: TodoPriority
    due_date: date | None
    category: TodoCategory
    tags: list[str]
    is_favorite: bool
    estimated_minutes: int | None