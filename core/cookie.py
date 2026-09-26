from fastapi import Response
from core.config import settings


def set_refresh_token_cookie(
    response: Response, 
    token: str, 
    max_age: int = settings.REFRESH_TOKEN_MAX_AGE,
    secure: bool | None = None,
) -> None:
    is_secure = (settings.ENVIRONMENT.lower() in ("prod", "production")) if secure is None else secure
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        expires=max_age,
        httponly=True,        
        secure=is_secure,       
        samesite="lax",     
        path="/auth",  
    )
    

def clear_refresh_token_cookie(response: Response, secure: bool | None = None) -> None:
    is_secure = (settings.ENVIRONMENT.lower() in ("prod", "production")) if secure is None else secure
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/auth",
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )