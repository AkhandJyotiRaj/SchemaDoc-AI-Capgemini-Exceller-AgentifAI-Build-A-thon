"""
Centralized error handling for SchemaDoc AI API.

Registers global exception handlers so every route returns consistent,
structured JSON error responses instead of raw tracebacks.
"""
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("SchemaDoc_API")


class SchemaDocError(Exception):
    """Base application error with structured fields."""

    def __init__(self, message: str, status_code: int = 500, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class PipelineExecutionError(SchemaDocError):
    """Raised when the LangGraph pipeline fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=500, details=details)


class DownstreamServiceError(SchemaDocError):
    """Raised when a downstream service (Gemini, DB, etc.) is unavailable."""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} unavailable: {message}",
            status_code=502,
            details={"service": service},
        )


class RateLimitExceededError(SchemaDocError):
    """Raised when a client exceeds rate limits."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please slow down.",
            status_code=429,
            details={"retry_after": retry_after},
        )


def _build_error_body(status_code: int, error: str, detail: str, extras: dict | None = None) -> dict:
    """Consistent error response shape."""
    body = {
        "error": error,
        "detail": detail,
        "status_code": status_code,
    }
    if extras:
        body.update(extras)
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    # ── 1. Our custom application errors ──
    @app.exception_handler(SchemaDocError)
    async def schemadoc_error_handler(request: Request, exc: SchemaDocError):
        logger.warning(f"SchemaDocError [{exc.status_code}]: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_body(
                exc.status_code,
                error=type(exc).__name__,
                detail=exc.message,
                extras=exc.details if exc.details else None,
            ),
        )

    # ── 2. FastAPI validation errors (malformed request bodies) ──
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        # Extract human-readable field errors
        field_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            field_errors.append(f"{loc}: {err.get('msg', 'invalid')}")

        logger.warning(f"Validation error on {request.url.path}: {field_errors}")
        return JSONResponse(
            status_code=422,
            content=_build_error_body(
                422,
                error="ValidationError",
                detail="Request validation failed.",
                extras={"field_errors": field_errors},
            ),
        )

    # ── 3. Standard HTTP exceptions (404, 403, etc.) ──
    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_body(
                exc.status_code,
                error="HTTPException",
                detail=str(exc.detail),
            ),
        )

    # ── 4. Catch-all for unhandled exceptions ──
    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        # Log the full traceback for debugging but return a safe message
        logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content=_build_error_body(
                500,
                error="InternalServerError",
                detail="An unexpected error occurred. Please try again later.",
            ),
        )
