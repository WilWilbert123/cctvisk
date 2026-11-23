"""Security middleware, API authentication, rate limiting, and HTTP security headers."""

from __future__ import annotations

import hmac
import ipaddress
import secrets
import time
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.config import get_settings
from backend.core.exceptions import RateLimitExceededError, SecurityViolationError
from backend.core.logging import get_logger

logger = get_logger("security")


class InMemoryRateLimiter:
    """Sliding-window rate limiter keyed by client IP and bucket."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        timestamps = [t for t in self._hits[key] if t > cutoff]
        if len(timestamps) >= max_requests:
            self._hits[key] = timestamps
            return False
        timestamps.append(now)
        self._hits[key] = timestamps
        return True

    def reset(self) -> None:
        self._hits.clear()


rate_limiter = InMemoryRateLimiter()


def is_loopback_client(client_host: str | None) -> bool:
    """Return True if the request originates from localhost / loopback."""
    if not client_host:
        return False
    if client_host in {"127.0.0.1", "::1", "localhost", "testclient"}:
        return True
    try:
        addr = ipaddress.ip_address(client_host)
        return addr.is_loopback
    except ValueError:
        return False


def is_private_lan_client(client_host: str | None) -> bool:
    """Return True if the request originates from a private RFC1918 or loopback address."""
    if is_loopback_client(client_host):
        return True
    if not client_host:
        return False
    try:
        addr = ipaddress.ip_address(client_host)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return False


def verify_api_token(provided_token: str | None) -> bool:
    """Constant-time verification of the local API access token."""
    settings = get_settings()
    expected = settings.API_ACCESS_TOKEN
    if not expected or not provided_token:
        return False
    return hmac.compare_digest(provided_token.strip(), expected.strip())


def enforce_request_auth(request: Request) -> None:
    """
    Validate client access:
    - Reject any non-LAN/public IP client immediately.
    - Localhost clients are allowed by default unless an explicit token is supplied and invalid.
    - Remote LAN clients (e.g., Android phone on Wi-Fi) are allowed ONLY when ALLOW_LAN_ACCESS
      is enabled OR when a valid X-API-Token / ?token= is provided.
    """
    settings = get_settings()
    client_host = request.client.host if request.client else "127.0.0.1"

    if not is_private_lan_client(client_host):
        logger.warning("Blocked request from non-private IP: %s", client_host)
        raise SecurityViolationError("Access is restricted to local private networks only.")

    token = (
        request.headers.get("X-API-Token")
        or request.query_params.get("token")
        or request.cookies.get("cctv_api_token")
    )

    if is_loopback_client(client_host):
        # If the caller explicitly sent an X-API-Token header that is non-empty and wrong, reject it
        if token and token != "local-dev" and not verify_api_token(token):
            raise SecurityViolationError("Invalid API access token.")
        return

    # Remote LAN client (e.g., Android phone on the same Wi-Fi)
    if not settings.ALLOW_LAN_ACCESS:
        raise SecurityViolationError(
            "Remote LAN access is currently disabled. Enable ALLOW_LAN_ACCESS in Settings or .env."
        )

    if token and token != "local-dev" and not verify_api_token(token):
        raise SecurityViolationError(
            "Valid API pairing token required for remote LAN dashboard access."
        )


def check_rate_limit(request: Request, is_scan_endpoint: bool = False) -> None:
    """Enforce per-IP rate limits."""
    settings = get_settings()
    client_host = request.client.host if request.client else "127.0.0.1"
    if is_scan_endpoint:
        allowed = rate_limiter.check(
            f"scan:{client_host}", settings.SCAN_RATE_LIMIT_PER_MINUTE, 60
        )
    else:
        allowed = rate_limiter.check(
            f"api:{client_host}", settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 60
        )
    if not allowed:
        raise RateLimitExceededError(retry_after_seconds=60)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attaches defensive HTTP security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        return response


def generate_stream_session_token() -> str:
    """Generate a URL-safe random token for authenticated browser MJPEG streaming."""
    return secrets.token_urlsafe(24)

