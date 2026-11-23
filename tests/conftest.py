"""Shared pytest fixtures providing an isolated in-memory SQLite database and FastAPI TestClient."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import get_settings
from backend.app.dependencies import get_db
from backend.app.main import create_application
from backend.core.security import rate_limiter
from backend.database.base import Base
import backend.models  # noqa: F401


@pytest.fixture()
def db_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    """Create a fresh isolated SQLite database and external vault key per test."""
    vault_key_file = tmp_path / ".test_vault.key"
    monkeypatch.setenv("VAULT_KEY_PATH", str(vault_key_file))
    monkeypatch.setenv("MONITORING_ENABLED", "false")
    get_settings.cache_clear()
    rate_limiter.reset()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient wired to the isolated test db_session."""
    app = create_application()

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client

