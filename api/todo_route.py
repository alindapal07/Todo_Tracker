from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import Response
from db.dependencies import get_db
from dependencies.auth_dependency import CurrentUser
from errors.exceptions import InvalidExportFormat
from repositories.todo_repositories import TodoRepository
from schemas.common_schema import SuccessResponse
from schemas.todo_schema import TodoCategory, TodoIn, TodoResponse, TodoUpdate
from service.todo_service import TodoService
from utils.responses import success_response

router = APIRouter(prefix="/todos", tags=["Todos"])


def get_todo_service(db: AsyncSession = Depends(get_db)) -> TodoService:
    repo = TodoRepository(db)
    return TodoService(repo)


@router.get("/categories", response_model=SuccessResponse[list[str]])
async def list_categories(
    service: TodoService = Depends(get_todo_service),
):
    categories = service.list_categories()
    return success_response(
        data=categories, message="Categories retrieved successfully"
    )


@router.get(
    "/categories/{category}", response_model=SuccessResponse[list[TodoResponse]]
)
async def get_todos_by_category(
    category: TodoCategory,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    todos = await service.get_todos_by_category(category, user_id=current_user.id)
    return success_response(data=todos, message="Todos retrieved successfully")


@router.delete("/categories/{category}", response_model=SuccessResponse[dict[str, Any]])
async def delete_todos_by_category(
    category: TodoCategory,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    result = await service.delete_todos_by_category(category, user_id=current_user.id)
    return success_response(data=result, message="Todos deleted successfully")


# ---------- Todo CRUD (Protected by CurrentUser) ----------


@router.post(
    "",
    response_model=SuccessResponse[TodoResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_todo(
    todo: TodoIn,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    created = await service.create_todo(todo, user_id=current_user.id)
    return success_response(data=created, message="Todo created successfully")


# get paginated list of todos with optional status, category, search, and created_at sorting
@router.get("", response_model=SuccessResponse[list[TodoResponse]])
async def get_todos(
    current_user: CurrentUser,
    completed: bool | None = Query(None, description="filter by completion status"),
    category: TodoCategory | None = Query(None, description="filter by category"),
    search: str | None = Query(
        None, min_length=1, description="search title/description"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    order_by: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="order by created_at: 'asc' or 'desc'",
    ),
    service: TodoService = Depends(get_todo_service),
):
    result = await service.list_todos(
        user_id=current_user.id,
        category=category,
        completed=completed,
        search=search,
        page=page,
        limit=limit,
        order_by=order_by,
    )
    return success_response(
        data=result["items"],
        message="Todos retrieved successfully",
        meta={
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"],
            "pages": result["pages"],
            "has_next": result["has_next"],
            "has_previous": result["has_previous"],
        },
    )


# export all todos for current user as json or csv file
@router.get("/export")
async def export_todo(
    current_user: CurrentUser,
    format: str = Query("json", description="export format: 'json' or 'csv'"),
    service: TodoService = Depends(get_todo_service),
):
    clean_format = format.strip().lower()
    if clean_format not in ("json", "csv"):
        raise InvalidExportFormat("Unsupported format. Please use 'json' or 'csv'")

    content = await service.export_todos(current_user.id, clean_format)

    if clean_format == "json":
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=todos.json"},
        )

    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=todos.csv"},
    )


@router.get("/{todo_id}", response_model=SuccessResponse[TodoResponse])
async def get_todo(
    todo_id: str,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    todo = await service.get_todo(todo_id, user_id=current_user.id)
    return success_response(data=todo, message="Todo retrieved successfully")


@router.put("/{todo_id}", response_model=SuccessResponse[TodoResponse])
async def replace_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    updated = await service.update_todo(todo_id, todo_update, user_id=current_user.id)
    return success_response(data=updated, message="Todo updated successfully")


@router.patch("/{todo_id}", response_model=SuccessResponse[TodoResponse])
async def update_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    updated = await service.update_todo(todo_id, todo_update, user_id=current_user.id)
    return success_response(data=updated, message="Todo updated successfully")


@router.delete("/{todo_id}", response_model=SuccessResponse[dict[str, Any]])
async def delete_todo(
    todo_id: str,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    result = await service.delete_todo(todo_id, user_id=current_user.id)
    return success_response(data=result, message="Todo deleted successfully")
