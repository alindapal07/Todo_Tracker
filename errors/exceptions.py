from typing import Any


class AppError(Exception):
    code: str = "APP_ERROR"
    message: str = "An application error occurred"

    def __init__(
        self,
        message: str | None = None,
        details: Any | None = None,
    ):
        if message is not None:
            self.message = message
        self.details = details
        super().__init__(self.message)


class UserAlreadyExists(AppError):
    code = "USER_ALREADY_EXISTS"
    message = "A user with this email or username already exists"


class UserNotFound(AppError):
    code = "USER_NOT_FOUND"
    message = "User not found"


class TodoNotFound(AppError):
    code = "TODO_NOT_FOUND"
    message = "Todo not found"


class TodoAlreadyExists(AppError):
    code = "TODO_ALREADY_EXISTS"
    message = "A Todo with this title already exists"


class CategoryNotFound(AppError):
    code = "CATEGORY_NOT_FOUND"
    message = "Category not found"


class CategoryAlreadyExists(AppError):
    code = "CATEGORY_ALREADY_EXISTS"
    message = "Category already exists"


class TokenInvalidated(AppError):
    code = "TOKEN_INVALIDATED"
    message = "Not authenticated: password changed"


class InvalidCurrentPassword(AppError):
    code = "INVALID_CURRENT_PASSWORD"
    message = "Current password is incorrect"


# raised when user requests an invalid export format like xml or pdf
class InvalidExportFormat(AppError):
    code = "INVALID_EXPORT_FORMAT"
    message = "Unsupported format. Please use 'json' or 'csv'"
