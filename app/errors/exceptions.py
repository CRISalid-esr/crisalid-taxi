"""Custom exceptions for the application."""

import json

from pydantic import ValidationError as PydanticValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_404_NOT_FOUND


class ApplicationError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Validation error."""

    def __init__(self, message: str):
        super().__init__(message, 400)


class NotFoundError(ApplicationError):
    """Not found error."""

    def __init__(self, message: str):
        super().__init__(message, 404)


async def invalid_entity_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for invalid entity errors (validation errors)."""
    if isinstance(exc, PydanticValidationError):
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": json.loads(exc.json())},
        )
    if isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error"},
    )


async def not_found_entity_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handler for not found errors."""
    return JSONResponse(
        status_code=HTTP_404_NOT_FOUND,
        content={"detail": exc.message},
    )
