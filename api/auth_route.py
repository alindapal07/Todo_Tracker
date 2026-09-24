from fastapi import APIRouter, HTTPException, status

from dependencies.auth_dependency import CurrentUser
from dependencies.user_dependencies import userServiceDependency
from schemas.auth_schema import Token, UserLogin, UserRegister, UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    user_data: UserRegister,
    user_service: userServiceDependency,
):
    try:
        created_user = await user_service.register_user(user_data)
        return created_user
    except ValueError as error:
        error_message = str(error)
        if "already exists" in error_message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Login and obtain JWT access token",
)
async def login(
    login_data: UserLogin,
    user_service: userServiceDependency,
):
    try:
        token = await user_service.login_user(login_data)
        return token
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_current_user_profile(
    current_user: CurrentUser,
):
    return current_user
