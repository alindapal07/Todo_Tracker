from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from models.todo_model import Todo
from repositories.todo_repositories import TodoRepository
from schemas.todo_schema import TodoCategory, TodoIn, TodoUpdate


class TodoService:

    def __init__(self, repository: TodoRepository):
        self.repository = repository

    @staticmethod
    def _validate_category(category: Any) -> TodoCategory:
        try:
            return TodoCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{category}' does not exist",
            )

    async def _get_or_404(self, todo_id: UUID) -> Todo:
        todo = await self.repository.get_by_id(todo_id)
        if todo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )
        return todo



    @staticmethod
    def list_categories() -> list[str]:
        return [category.value for category in TodoCategory]

    async def get_todos_by_category(self, category: Any) -> list[Todo]:
        valid = self._validate_category(category)
        return await self.repository.get_by_category(valid)

    async def delete_todos_by_category(self, category: Any) -> dict[str, Any]:
        valid = self._validate_category(category)
        deleted_count = await self.repository.delete_by_category(valid)

        return {
            "message": "Todos deleted successfully",
            "category": valid.value,
            "deleted_count": deleted_count,
        }



    async def create_todo(self, payload: TodoIn) -> Todo:
        category = self._validate_category(payload.category)

        existing = await self.repository.get_by_title(payload.title)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A Todo with this title already exists",
            )

        data = payload.model_dump(exclude_unset=True)
        data["category"] = category

        return await self.repository.create(Todo(**data))

    async def get_all_todos(self) -> list[Todo]:
        return await self.repository.get_all()

    async def get_todo(self, todo_id: UUID) -> Todo:
        return await self._get_or_404(todo_id)


    async def list_todos(
        self,
        *,
        category: Any | None = None,
        completed: bool | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> dict[str, Any]:
        valid_category = (
            self._validate_category(category) if category is not None else None
        )

        items, total = await self.repository.list(
            category=valid_category,
            completed=completed,
            search=search,
            page=page,
            limit=limit,
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
        }

    async def update_todo(self, todo_id: UUID, payload: TodoUpdate) -> Todo:
        todo = await self._get_or_404(todo_id)

        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update",
            )

        if "category" in changes:
            changes["category"] = self._validate_category(changes["category"])

        new_title = changes.get("title")
        if new_title and new_title.lower() != todo.title.lower():
            clash = await self.repository.get_by_title(new_title)
            if clash is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A Todo with this title already exists",
                )

        return await self.repository.update(todo, changes)

    async def delete_todo(self, todo_id: UUID) -> dict[str, Any]:
        todo = await self._get_or_404(todo_id)
        await self.repository.delete(todo)

        return {
            "message": "Todo deleted successfully",
            "todo_id": str(todo.id),
        }