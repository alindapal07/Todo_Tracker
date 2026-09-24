from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.dependencies import get_db
from dependencies.auth_dependency import CurrentUser
from repositories.todo_repositories import TodoRepository
from schemas.todo_schema import TodoCategory, TodoIn, TodoResponse, TodoUpdate
from service.todo_service import TodoService


router = APIRouter(prefix="/todos", tags=["Todos"])


def get_todo_service(db: AsyncSession = Depends(get_db)) -> TodoService:
    repo = TodoRepository(db)
    return TodoService(repo)


@router.get("/categories")
async def list_categories(
    service: TodoService = Depends(get_todo_service),
):
    return service.list_categories()


@router.get("/categories/{category}", response_model=list[TodoResponse])
async def get_todos_by_category(
    category: TodoCategory,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    return await service.get_todos_by_category(category, user_id=current_user.id)


@router.delete("/categories/{category}")
async def delete_todos_by_category(
    category: TodoCategory,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    return await service.delete_todos_by_category(category, user_id=current_user.id)


# ---------- Todo CRUD (Protected by CurrentUser) ----------

@router.post("", response_model=TodoResponse, status_code=201)
async def create_todo(
    todo: TodoIn,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    return await service.create_todo(todo, user_id=current_user.id)


@router.get("", response_model=list[TodoResponse])
async def get_todos(
    current_user: CurrentUser,
    completed: bool | None = Query(None, description="filter by completion status"),
    search: str | None = Query(None, min_length=1, description="search title/description"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    service: TodoService = Depends(get_todo_service),
):
    result = await service.list_todos(
        user_id=current_user.id,
        completed=completed,
        search=search,
        page=page,
        limit=limit,
    )
    return result["items"]


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: str,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    return await service.get_todo(todo_id, user_id=current_user.id)


@router.put("/{todo_id}", response_model=TodoResponse)
async def replace_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    return await service.update_todo(todo_id, todo_update, user_id=current_user.id)


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    return await service.update_todo(todo_id, todo_update, user_id=current_user.id)


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user: CurrentUser,
    service: TodoService = Depends(get_todo_service),
):
    return await service.delete_todo(todo_id, user_id=current_user.id)