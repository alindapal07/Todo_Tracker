from typing import Any, TypeVar

from schemas.common_schema import SuccessResponse

T = TypeVar("T")


def success_response[T](
    data: T | None = None,
    *,
    message: str = "Success",
    meta: dict[str, Any] | None = None,
) -> SuccessResponse:
    return SuccessResponse(success=True, message=message, data=data, meta=meta)