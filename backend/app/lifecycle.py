"""FastAPI application lifespan management (startup and shutdown hooks)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.config import get_settings
from backend.core.logging import configure_logging
from backend.database.database import init_db
from backend.workers.monitoring_worker import start_monitoring_worker, stop_monitoring_worker


@asynccontextmanager
async def app_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize logging, SQLite database schema, and background monitoring on startup."""
    settings = get_settings()
    logger = configure_logging(settings.LOG_LEVEL, settings.LOG_FILE_PATH)
    logger.info("Initializing %s v%s...", settings.APP_NAME, settings.APP_VERSION)

    init_db()

    if settings.MONITORING_ENABLED:
        start_monitoring_worker()

    logger.info(
        "Local API Pairing Token for remote LAN / Android PWA access: %s",
        settings.API_ACCESS_TOKEN,
    )
    try:
        yield
    finally:
        await stop_monitoring_worker()
        logger.info("Shutting down %s cleanly.", settings.APP_NAME)

