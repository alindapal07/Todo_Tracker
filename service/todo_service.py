from typing import Any
import json
import csv
import io
from fastapi import HTTPException, status

from errors.exceptions import CategoryNotFound, InvalidExportFormat, TodoAlreadyExists, TodoNotFound
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
            raise CategoryNotFound(f"Category '{category}' does not exist")

    async def _get_or_404(self, todo_id: str, user_id: str) -> Todo:
        todo = await self.repository.get_by_id(todo_id)
        if todo is None:
            raise TodoNotFound()

        if todo.user_id is not None and todo.user_id != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this todo",
            )

        return todo

    @staticmethod
    def list_categories() -> list[str]:
        return [category.value for category in TodoCategory]

    async def get_todos_by_category(
        self,
        category: Any,
        user_id: str,
    ) -> list[Todo]:
        valid = self._validate_category(category)
        return await self.repository.get_by_category(valid, user_id=user_id)

    async def delete_todos_by_category(
        self,
        category: Any,
        user_id: str,
    ) -> dict[str, Any]:
        valid = self._validate_category(category)
        deleted_count = await self.repository.delete_by_category(valid, user_id=user_id)

        return {
            "category": valid.value,
            "deleted_count": deleted_count,
        }

    async def create_todo(self, payload: TodoIn, user_id: str) -> Todo:
        category = self._validate_category(payload.category)

        existing = await self.repository.get_by_title(payload.title, user_id=user_id)
        if existing is not None:
            raise TodoAlreadyExists("A Todo with this title already exists")

        data = payload.model_dump(exclude_unset=True)
        data["category"] = category
        data["user_id"] = str(user_id)

        return await self.repository.create(Todo(**data))

    async def get_all_todos(self, user_id: str) -> list[Todo]:
        return await self.repository.get_all(user_id=user_id)

    async def get_todo(self, todo_id: str, user_id: str) -> Todo:
        return await self._get_or_404(todo_id, user_id)

    # fetch todos with pagination, keyword search, status filters, and created_at sorting
    async def list_todos(
        self,
        *,
        user_id: str,
        category: Any | None = None,
        completed: bool | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 10,
        order_by: str = "desc",
    ) -> dict[str, Any]:
        valid_category = (
            self._validate_category(category) if category is not None else None
        )

        items, total, has_next, has_previous = await self.repository.list(
            user_id=user_id,
            category=valid_category,
            completed=completed,
            search=search,
            page=page,
            limit=limit,
            order_by=order_by,
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
            "has_next": has_next,
            "has_previous": has_previous,
        }

    async def update_todo(
        self,
        todo_id: str,
        payload: TodoUpdate,
        user_id: str,
    ) -> Todo:
        todo = await self._get_or_404(todo_id, user_id)

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
            clash = await self.repository.get_by_title(new_title, user_id=user_id)
            if clash is not None and clash.id != todo.id:
                raise TodoAlreadyExists("A Todo with this title already exists")

        return await self.repository.update(todo, changes)

    async def delete_todo(self, todo_id: str, user_id: str) -> dict[str, Any]:
        todo = await self._get_or_404(todo_id, user_id)
        await self.repository.delete(todo)

        return {
            "todo_id": str(todo.id),
        }

    # export all todos for user in json or csv format
    async def export_todos(self, user_id: str, file_format: str) -> str:
        todos = await self.repository.get_all(user_id)
        fmt = file_format.strip().lower()

        if fmt == "json":
            data = []
            for todo in todos:
                data.append(
                    {
                        "todo_id": str(todo.id),
                        "title": todo.title,
                        "description": todo.description,
                        "status": getattr(todo.status, "value", todo.status),
                        "priority": getattr(todo.priority, "value", todo.priority),
                        "due_date": (
                            todo.due_date.isoformat() if todo.due_date else None
                        ),
                        "category": getattr(todo.category, "value", todo.category),
                        "tags": todo.tags or [],
                        "is_favorite": todo.is_favorite,
                        "estimated_minutes": todo.estimated_minutes,
                    }
                )
            return json.dumps(data, indent=2)

        if fmt == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "todo_id",
                    "title",
                    "description",
                    "status",
                    "priority",
                    "due_date",
                    "category",
                    "tags",
                    "is_favorite",
                    "estimated_minutes",
                ]
            )
            for todo in todos:
                writer.writerow(
                    [
                        str(todo.id),
                        todo.title,
                        todo.description or "",
                        getattr(todo.status, "value", todo.status),
                        getattr(todo.priority, "value", todo.priority),
                        todo.due_date.isoformat() if todo.due_date else "",
                        getattr(todo.category, "value", todo.category),
                        ", ".join(todo.tags) if todo.tags else "",
                        todo.is_favorite,
                        todo.estimated_minutes or "",
                    ]
                )
            return output.getvalue()

        raise InvalidExportFormat("Unsupported format. Please use 'json' or 'csv'")
             
