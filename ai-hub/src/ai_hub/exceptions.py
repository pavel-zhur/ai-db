"""Exception handling for AI-Hub."""

import logging
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from .models import ErrorResponse

logger = logging.getLogger(__name__)


class AIHubError(Exception):
    """Base exception for AI-Hub errors."""

    def __init__(
        self,
        message: str,
        error_details: Optional[dict[str, Any]] = None,
        status_code: int = 500
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_details = error_details or {}
        self.status_code = status_code


class ConfigurationError(AIHubError):
    """Configuration-related errors."""

    def __init__(self, message: str, error_details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_details, status_code=500)


class ValidationError(AIHubError):
    """Input validation errors."""

    def __init__(self, message: str, error_details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_details, status_code=400)


class RepositoryError(AIHubError):
    """Git repository-related errors."""

    def __init__(self, message: str, error_details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_details, status_code=500)


class DatabaseError(AIHubError):
    """Database operation errors."""

    def __init__(self, message: str, error_details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_details, status_code=500)


class PermissionError(AIHubError):
    """Permission-related errors."""

    def __init__(self, message: str, error_details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_details, status_code=403)


def create_user_friendly_error(exception: Exception) -> tuple[str, dict[str, Any], str]:
    """Create user-friendly error message from exception.

    Returns:
        tuple: (user_friendly_message, technical_details, error_type)
    """
    error_type = type(exception).__name__
    technical_details = {
        "exception_type": error_type,
        "exception_message": str(exception),
    }

    # Add additional details for known exception types
    if hasattr(exception, '__dict__'):
        technical_details.update({
            k: v for k, v in exception.__dict__.items()
            if not k.startswith('_') and k not in ['args']
        })

    # Create user-friendly messages based on exception type
    user_friendly_message = _get_user_friendly_message(exception, error_type)

    return user_friendly_message, technical_details, error_type


def _get_user_friendly_message(exception: Exception, error_type: str) -> str:
    """Get user-friendly error message based on exception type."""
    error_message = str(exception).lower()

    # AI-DB specific errors
    if "permission" in error_message:
        return (
            "You don't have permission to perform this operation. "
            "Please check your access level."
        )

    if "schema" in error_message or "validation" in error_message:
        return "The data doesn't match the expected format. Please check your input and try again."

    if "constraint" in error_message:
        return (
            "This operation would violate database constraints. "
            "Please check your data relationships."
        )

    if "compilation" in error_message:
        return "Unable to understand your query. Please rephrase it or check the syntax."

    # Git-layer specific errors
    if "repository" in error_message or "git" in error_message:
        return "There was an issue accessing the data repository. Please try again later."

    if "transaction" in error_message:
        return "Unable to complete the operation due to a conflict. Please try again."

    if "lock" in error_message:
        return "Another operation is currently in progress. Please wait and try again."

    # Network/API errors
    if "timeout" in error_message or "connection" in error_message:
        return "The operation took too long to complete. Please try again with a simpler request."

    if "api" in error_message or "key" in error_message:
        return "There was an issue with the AI service. Please check configuration and try again."

    # Validation errors
    if "validation_error" in error_type.lower() or "valueerror" in error_type.lower():
        return "Invalid input provided. Please check your request format and try again."

    # HTTP errors
    if "http" in error_type.lower():
        return "A network error occurred. Please check your connection and try again."

    # File system errors
    if "file" in error_message or "directory" in error_message:
        return "Unable to access required files. Please check the system configuration."

    # Generic error
    return (
        "An unexpected error occurred. Please try again or contact support "
        "if the problem persists."
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for all unhandled exceptions."""
    logger.exception(f"Unhandled exception in {request.url.path}: {exc}")

    # Handle AIHubError instances
    if isinstance(exc, AIHubError):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.message,
                error_details=exc.error_details,
                error_type=type(exc).__name__
            ).model_dump()
        )

    # Handle HTTPException instances
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.detail,
                error_type="HTTPException"
            ).model_dump()
        )

    # Handle all other exceptions
    user_friendly_message, technical_details, error_type = create_user_friendly_error(exc)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=user_friendly_message,
            error_details=technical_details,
            error_type=error_type
        ).model_dump()
    )
