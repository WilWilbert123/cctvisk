"""Centralized exception hierarchy and FastAPI exception handlers."""

from __future__ import annotations

from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "APPLICATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class UnauthorizedSubnetError(AppException):
    """Raised when a requested IP or subnet is not an authorized private/local network."""

    def __init__(self, target: str) -> None:
        super().__init__(
            message=(
                f"Target '{target}' is outside authorized private/local RFC1918 networks. "
                "Public internet scanning is strictly prohibited."
            ),
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="UNAUTHORIZED_NETWORK_TARGET",
            details={"target": target},
        )


class ResourceNotFoundError(AppException):
    """Raised when a requested entity does not exist."""

    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class ScanInProgressError(AppException):
    """Raised when attempting to start a network scan while one is already running."""

    def __init__(self) -> None:
        super().__init__(
            message="A network scan is already in progress. Cancel or wait for it to finish.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="SCAN_ALREADY_RUNNING",
        )


class SecurityViolationError(AppException):
    """Raised when an authentication, authorization, or SSRF policy check fails."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="SECURITY_VIOLATION",
        )


class RateLimitExceededError(AppException):
    """Raised when a client exceeds the configured request rate limit."""

    def __init__(self, retry_after_seconds: int = 60) -> None:
        super().__init__(
            message="Rate limit exceeded. Please wait before issuing additional requests.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after_seconds},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach structured JSON exception handlers to the FastAPI app."""

    @app.exception_handler(AppException)
    async def handle_app_exception(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        sanitized_errors = []
        for err in exc.errors():
            sanitized_errors.append(
                {
                    "loc": [str(x) for x in err.get("loc", [])],
                    "msg": err.get("msg", "Invalid value"),
                    "type": err.get("type", "value_error"),
                }
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed. Check your input parameters.",
                    "details": {"errors": sanitized_errors},
                },
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_request: Request, exc: Exception) -> JSONResponse:
        # Never leak internal stack traces or sensitive variables in API responses
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred while processing the request.",
                    "details": {"type": type(exc).__name__},
                },
            },
        )

