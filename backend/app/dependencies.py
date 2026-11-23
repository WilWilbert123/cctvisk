"""FastAPI dependency injection providers for database sessions, authentication, and rate limiting."""

from __future__ import annotations

from collections.abc import Generator
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from backend.core.security import check_rate_limit, enforce_request_auth
from backend.database.session import get_db_session


def get_db(session: Session = Depends(get_db_session)) -> Generator[Session, None, None]:
    """Provide a transactional SQLAlchemy Session."""
    yield session


def require_authorized_client(request: Request) -> None:
    """Enforce local/LAN client authentication and standard API rate limiting."""
    enforce_request_auth(request)
    check_rate_limit(request, is_scan_endpoint=False)


def require_scan_rate_limit(request: Request) -> None:
    """Enforce stricter rate limiting on active network scan initiation endpoints."""
    enforce_request_auth(request)
    check_rate_limit(request, is_scan_endpoint=True)

