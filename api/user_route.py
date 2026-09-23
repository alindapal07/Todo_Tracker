from fastapi import APIRouter, HTTPException, status

from schemas.user_schema import (
    userBase,
    userIn,
    userResponse,
)

from dependencies.user_dependencies import userServiceDependency


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/user/register",
    response_model=userResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: userBase,
    user_service: userServiceDependency
):
    try:
        created_user = await user_service.register_user(
            user_data
        )

        return created_user

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.post(
    "/user/login",
    response_model=userResponse
)
async def login_user(
    user_data: userIn,
    user_service: userServiceDependency
):
    try:
        logged_in_user = await user_service.login_user(
            user_data
        )

        return logged_in_user

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )