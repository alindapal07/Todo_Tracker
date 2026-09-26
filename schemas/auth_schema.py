from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class TokenData(BaseModel):
    user_id: str | None = None
    username: str | None = None


class UserLogin(BaseModel):
    username: str = Field(
        ...,
        description="Username or registered email address",
    )
    password: str = Field(
        ...,
        description="User password",
    )


class UserRegister(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username",
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password with at least 8 characters",
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Optional display name",
    )


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    name: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
