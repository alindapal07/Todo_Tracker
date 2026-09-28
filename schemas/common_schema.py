from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class SuccessResponse[T](BaseModel):
    success: bool = True
    message: str
    data: T | None = None
    meta: dict[str, Any] | None = None

    