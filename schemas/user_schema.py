from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class userBase(BaseModel):
    name: str = Field(
        min_length=5,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=100
    )


class userIn(BaseModel):
    email: EmailStr
    password: str


class userUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=5,
        max_length=50
    )

    email: EmailStr | None = None

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=100
    )


class userResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )