"""SQLAlchemy session factory and FastAPI dependency generator."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from sqlalchemy.orm import Session, sessionmaker
from backend.database.database import get_engine


def get_session_factory() -> sessionmaker[Session]:
    """Return a configured sessionmaker bound to the active engine."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for background workers and services needing a database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

