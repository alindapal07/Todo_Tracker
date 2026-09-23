from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.dependencies import get_db
from repositories.user_repositories import UserRepository
from service.user_service import userService


def get_user_service(
    db_session: Annotated[AsyncSession, Depends(get_db)]
):
    repo = UserRepository(db=db_session)

    return userService(repo)


userServiceDependency = Annotated[
    userService,
    Depends(get_user_service)
]