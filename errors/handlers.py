from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from errors.exceptions import (
    AppError,
    CategoryAlreadyExists,
    CategoryNotFound,
    TodoAlreadyExists,
    TodoNotFound,
    UserAlreadyExists,
    UserNotFound,
)
from errors.response import ErrorDetail, ErrorResponse

ERROR_STATUS_CODES: dict[type[AppError], int] = {
    UserAlreadyExists: status.HTTP_409_CONFLICT,
    UserNotFound: status.HTTP_404_NOT_FOUND,
    TodoNotFound: status.HTTP_404_NOT_FOUND,
    TodoAlreadyExists: status.HTTP_409_CONFLICT,
    CategoryNotFound: status.HTTP_404_NOT_FOUND,
    CategoryAlreadyExists: status.HTTP_409_CONFLICT,
}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = ERROR_STATUS_CODES.get(type(exc))
    if status_code is None:
        for err_cls, code in ERROR_STATUS_CODES.items():
            if isinstance(exc, err_cls):
                status_code = code
                break
    if status_code is None:
        status_code = getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST)

    response = ErrorResponse(
        error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
    )

    return JSONResponse(
        status_code=status_code, content=response.model_dump(mode="json")
    )


async def unexpected_error_handler(request: Request, exc: Exception):
    print(str(exc))

    response = ErrorResponse(
        error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message="Internal server error")
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    validation_errors = []

    for error in exc.errors():
        validation_errors.append(
            {
                "location": list(error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=validation_errors,
        )
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)