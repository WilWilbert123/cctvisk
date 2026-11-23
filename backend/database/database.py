"""SQLite database engine management, initialization, and health verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from sqlalchemy import Engine, create_engine, event, text
from backend.app.config import get_settings
from backend.core.logging import get_logger
from backend.database.base import Base

logger = get_logger("database")

_engine: Engine | None = None


def _configure_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()


def get_engine(database_url: str | None = None) -> Engine:
    """Create or return the singleton SQLAlchemy engine."""
    global _engine
    settings = get_settings()
    url = database_url or settings.DATABASE_URL

    if _engine is not None and database_url is None:
        return _engine

    if url.startswith("sqlite:///") and ":memory:" not in url:
        db_file = Path(url.replace("sqlite:///", ""))
        db_file.parent.mkdir(parents=True, exist_ok=True)

    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)

    if url.startswith("sqlite"):
        event.listen(engine, "connect", _configure_sqlite_pragma)

    if database_url is None:
        _engine = engine
    return engine


def init_db(engine: Engine | None = None) -> None:
    """Import all models and ensure database tables and indexes exist."""
    import backend.models  # noqa: F401

    target_engine = engine or get_engine()
    Base.metadata.create_all(bind=target_engine)
    logger.info("Database schema verified and initialized.")


def check_db_health(engine: Engine | None = None) -> dict[str, Any]:
    """Run a diagnostic query on SQLite and return file size and table counts."""
    target_engine = engine or get_engine()
    settings = get_settings()
    try:
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            device_count = conn.execute(text("SELECT COUNT(*) FROM devices")).scalar() or 0
            camera_count = conn.execute(text("SELECT COUNT(*) FROM cameras")).scalar() or 0
            scan_count = conn.execute(text("SELECT COUNT(*) FROM network_scans")).scalar() or 0

        db_path_str = settings.DATABASE_URL.replace("sqlite:///", "")
        db_path = Path(db_path_str)
        size_bytes = db_path.stat().st_size if db_path.exists() else 0

        return {
            "healthy": True,
            "engine": "SQLite (WAL Mode)",
            "database_path": str(db_path),
            "size_bytes": size_bytes,
            "tables_initialized": True,
            "records": {
                "devices": int(device_count),
                "cameras": int(camera_count),
                "scans": int(scan_count),
            },
        }
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return {
            "healthy": False,
            "engine": "SQLite",
            "error": str(exc),
        }

