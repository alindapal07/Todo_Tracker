from typing import Any

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

    async def get_all(self, user_id: str | None = None) -> list[Todo]:
        statement = select(Todo)
        if user_id is not None:
            statement = statement.where(Todo.user_id == user_id)
        result = await self.db.execute(statement.order_by(Todo.id))
        return list(result.scalars().all())

    async def get_by_id(self, todo_id: str) -> Todo | None:
        statement = select(Todo).where(Todo.id == str(todo_id))
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_title(self, title: str, user_id: str | None = None) -> Todo | None:
        statement = select(Todo).where(func.lower(Todo.title) == title.lower())
        if user_id is not None:
            statement = statement.where(Todo.user_id == user_id)
        result = await self.db.execute(statement)
        return result.scalars().first()

    async def get_by_category(
        self,
        category: TodoCategory,
        user_id: str | None = None,
    ) -> list[Todo]:
        statement = select(Todo).where(Todo.category == category)
        if user_id is not None:
            statement = statement.where(Todo.user_id == user_id)
        result = await self.db.execute(statement.order_by(Todo.id))
        return list(result.scalars().all())

    # fetch page of todos with optional status and text search, sorted by created_at
    async def list(
        self,
        *,
        user_id: str | None = None,
        category: TodoCategory | None = None,
        completed: bool | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 10,
        order_by: str = "desc",
    ) -> tuple[list[Todo], int, bool, bool]:
        filters = []

        # filter by current user
        if user_id is not None:
            filters.append(Todo.user_id == user_id)

        # filter by category
        if category is not None:
            filters.append(Todo.category == category)

        # filter by completed or pending status
        if completed is not None:
            if completed:
                filters.append(Todo.status == TodoStatus.completed)
            else:
                filters.append(Todo.status != TodoStatus.completed)

        # search keyword in title or description
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

        # count total matching rows for pagination
        total = int(await self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)

        # sort by created_at timestamp in ascending or descending order
        if str(order_by).strip().lower() == "asc":
            order_clause = [Todo.created_at.asc(), Todo.id.asc()]
        else:
            order_clause = [Todo.created_at.desc(), Todo.id.desc()]

        # apply sorting, offset, and limit to fetch the requested page
        result = await self.db.execute(
            base.order_by(*order_clause).offset((page - 1) * limit).limit(limit)
        )

        todos = list(result.scalars().all())

        has_next = page * limit < total
        has_previous = page > 1 and total > 0
        return todos, total, has_next, has_previous

    async def count_by_category(
        self,
        category: TodoCategory,
        user_id: str | None = None,
    ) -> int:
        statement = (
            select(func.count()).select_from(Todo).where(Todo.category == category)
        )
        if user_id is not None:
            statement = statement.where(Todo.user_id == user_id)
        total = await self.db.scalar(statement)
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

    async def delete_by_category(
        self,
        category: TodoCategory,
        user_id: str | None = None,
    ) -> int:
        statement = delete(Todo).where(Todo.category == category)
        if user_id is not None:
            statement = statement.where(Todo.user_id == user_id)
        result = await self.db.execute(statement)
        await self.db.commit()

        return int(result.rowcount or 0)

