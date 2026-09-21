from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.todo_model import Todo
from schemas.todo_schema import TodoCategory, TodoStatus


class TodoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, todo: Todo) -> Todo:
        self.db.add(todo)
        await self.db.commit()
        await self.db.refresh(todo)

        return todo


    async def get_all(self) -> list[Todo]:
        result = await self.db.execute(select(Todo).order_by(Todo.id))
        return list(result.scalars().all())

    async def get_by_id(self, todo_id: UUID) -> Todo | None:
        return await self.db.get(Todo, todo_id)

    async def get_by_title(self, title: str) -> Todo | None:
        result = await self.db.execute(
            select(Todo).where(func.lower(Todo.title) == title.lower())
        )
        return result.scalars().first()

    async def get_by_category(self, category: TodoCategory) -> list[Todo]:
        result = await self.db.execute(
            select(Todo).where(Todo.category == category).order_by(Todo.id)
        )
        return list(result.scalars().all())

    async def list(
        self,
        *,
        category: TodoCategory | None = None,
        completed: bool | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[Todo], int]:

        filters = []

        if category is not None:
            filters.append(Todo.category == category)

        if completed is not None:
            if completed:
                filters.append(Todo.status == TodoStatus.completed)
            else:
                filters.append(Todo.status != TodoStatus.completed)

        if search:
            pattern = f"%{search.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(Todo.title).like(pattern),
                    func.lower(Todo.description).like(pattern),
                )
            )

        base = select(Todo)
        if filters:
            base = base.where(*filters)

        total = await self.db.scalar(
            select(func.count()).select_from(base.subquery())
        )

        result = await self.db.execute(
            base.order_by(Todo.id).offset((page - 1) * limit).limit(limit)
        )

        return list(result.scalars().all()), int(total or 0)

    async def count_by_category(self, category: TodoCategory) -> int:
        total = await self.db.scalar(
            select(func.count())
            .select_from(Todo)
            .where(Todo.category == category)
        )
        return int(total or 0)


    async def update(self, todo: Todo, changes: dict[str, Any]) -> Todo:
        for field, value in changes.items():
            setattr(todo, field, value)

        await self.db.commit()
        await self.db.refresh(todo)

        return todo


    async def delete(self, todo: Todo) -> None:
        await self.db.delete(todo)
        await self.db.commit()

    async def delete_by_category(self, category: TodoCategory) -> int:
        result = await self.db.execute(
            delete(Todo).where(Todo.category == category)
        )
        await self.db.commit()

        return int(result.rowcount or 0)