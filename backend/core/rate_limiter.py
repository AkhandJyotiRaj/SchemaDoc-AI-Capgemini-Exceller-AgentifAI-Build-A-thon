"""
Rate limiting middleware for SchemaDoc AI API.

Uses slowapi (a FastAPI-native wrapper around the 'limits' library) to enforce
per-IP sliding-window rate limits. Configurable per-endpoint.

JUSTIFICATION:
- slowapi is battle-tested, supports multiple storage backends (in-memory, Redis),
  and integrates directly with FastAPI's dependency injection.
- IP-based limiting is chosen over auth-based quotas because the app currently
  has no authentication layer. This provides immediate abuse protection.
- Limits are configurable via environment variables for production tuning.

TRADE-OFFS:
- IP-based can be circumvented by rotating IPs; for stronger protection,
  add API-key authentication in a future iteration.
- In-memory storage resets on server restart; use Redis for persistence at scale.
"""
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("SchemaDoc_API")

# ── Limiter instance (IP-based, in-memory storage) ──
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # generous default for read endpoints
    storage_uri="memory://",        # swap to "redis://..." for production
)


# ── Per-endpoint limit constants (configurable) ──
# Heavy endpoints (AI calls, DB connections) get stricter limits
PIPELINE_RUN_LIMIT = "5/minute"     # pipeline runs are expensive (Gemini + DB)
CHAT_LIMIT = "20/minute"            # each chat message calls Gemini
EXPORT_REPORT_LIMIT = "10/minute"   # report generation calls Gemini
SCHEMA_OVERVIEW_LIMIT = "15/minute" # overview calls Gemini
READ_LIMIT = "60/minute"            # standard read endpoints


def _custom_rate_limit_response(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a structured 429 response consistent with our error format."""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)} on {request.url.path}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "RateLimitExceeded",
            "detail": f"Rate limit exceeded: {exc.detail}. Please slow down.",
            "status_code": 429,
        },
        headers={"Retry-After": "60"},
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Attach the rate limiter to the FastAPI application.
    Call this during app setup in main.py.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _custom_rate_limit_response)
    logger.info("Rate limiting enabled (IP-based, in-memory).")
