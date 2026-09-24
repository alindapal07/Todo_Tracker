from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from core.security import decode_access_token
from dependencies.user_dependencies import userServiceDependency
from models.user_model import User


bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
    user_service: userServiceDependency,
) -> User:
    authentication_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if credentials is None or not credentials.credentials:
        raise authentication_error

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except Exception:
        raise authentication_error

    if not payload:
        raise authentication_error

    user_id = payload.get("sub")

    if not user_id:
        raise authentication_error

    user = await user_service.get_user_by_id(str(user_id))

    if not user:
        raise authentication_error

    if hasattr(user, "is_active") and not user.is_active:
        raise authentication_error

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
