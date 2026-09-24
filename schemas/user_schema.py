from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from schemas.auth_schema import Token, UserRegister, UserResponse


class userBase(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=50,
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=100,
    )


class userIn(BaseModel):
    email: EmailStr
    password: str


class userUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    email: EmailStr | None = None
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
    )


class userResponse(BaseModel):
    id: str
    username: str | None = None
    name: str | None = None
    email: EmailStr
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    user: userResponse
    access_token: str
    token_type: str = "bearer"


__all__ = [
    "userBase",
    "userIn",
    "userUpdate",
    "userResponse",
    "AuthResponse",
    "Token",
    "UserRegister",
    "UserResponse",
]