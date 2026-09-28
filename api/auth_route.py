from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status

from core.config import settings
from core.cookie import clear_refresh_token_cookie, set_refresh_token_cookie
from dependencies.auth_dependency import CurrentUser
from dependencies.user_dependencies import userServiceDependency
from schemas.auth_schema import (
    PasswordChangeRequest,
    RefreshTokenRequest,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)


from schemas.common_schema import SuccessResponse
from utils.responses import success_response


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    user_data: UserRegister,
    user_service: userServiceDependency,
):
    created_user = await user_service.register_user(user_data)
    return success_response(
        data=created_user,
        message="User registered successfully",
    )


@router.post(
    "/login",
    response_model=SuccessResponse[Token],
    summary="Login and obtain JWT access token",
)
async def login(
    request: Request,
    response: Response,
    login_data: UserLogin,
    user_service: userServiceDependency,
):
    try:
        ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        token_payload, raw_refresh_token = await user_service.login_user(
            login_data=login_data,
            ip=ip,
            user_agent=user_agent,
        )

        set_refresh_token_cookie(response, raw_refresh_token)
        return success_response(
            data=Token(**token_payload),
            message="Login successful",
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/refresh",
    response_model=SuccessResponse[Token],
    summary="Rotate refresh token and issue new access token",
)
async def refresh(
    request: Request,
    response: Response,
    user_service: userServiceDependency,
    body: RefreshTokenRequest | None = None,
    cookie_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
):
    raw_refresh_token = (
        (body.refresh_token if body and body.refresh_token else None)
        or cookie_token
        or request.cookies.get(settings.REFRESH_COOKIE_NAME)
        or request.cookies.get("refresh_token")
        or request.cookies.get("refresh-token")
    )

    if not raw_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    try:
        token_payload, new_raw_token = await user_service.refresh_token(
            raw_refresh_token=raw_refresh_token,
            ip_address=ip,
            user_agent=user_agent,
        )
        set_refresh_token_cookie(response, new_raw_token)
        return success_response(
            data=Token(
                access_token=token_payload["access_token"],
                refresh_token=new_raw_token,
                token_type="bearer",
            ),
            message="Token refreshed successfully",
        )
    except ValueError as error:
        clear_refresh_token_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    response_model=SuccessResponse[dict[str, str]],
    summary="Logout and revoke active refresh token",
)
async def logout(
    request: Request,
    response: Response,
    user_service: userServiceDependency,
    body: RefreshTokenRequest | None = None,
    cookie_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
):
    raw_refresh_token = (
        (body.refresh_token if body and body.refresh_token else None)
        or cookie_token
        or request.cookies.get(settings.REFRESH_COOKIE_NAME)
        or request.cookies.get("refresh_token")
        or request.cookies.get("refresh-token")
    )

    if raw_refresh_token:
        try:
            await user_service.revoke_token(raw_refresh_token)
        except Exception:
            pass

    clear_refresh_token_cookie(response)
    return success_response(message="Logged out successfully")


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get current authenticated user profile",
)
async def get_current_user_profile(
    current_user: CurrentUser,
):
    return success_response(
        data=current_user,
        message="User profile retrieved successfully",
    )


@router.post(
    "/change-password",
    response_model=SuccessResponse[dict[str, str]],
    summary="Change user password and invalidate previous sessions",
)
async def change_password(
    response: Response,
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    user_service: userServiceDependency,
):
    await user_service.change_password(
        user=current_user,
        data=password_data,
    )
    clear_refresh_token_cookie(response)
    return success_response(message="Password changed successfully")


