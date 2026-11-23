"""Application health check aggregating database, workers, and external binary status."""

from __future__ import annotations

from typing import Any
from backend.app.config import get_settings
from backend.core.events import event_manager
from backend.database.database import check_db_health
from backend.services.cameras.camera_connection import resolve_ffmpeg_binary
from backend.services.monitoring.monitor_scheduler import monitor_scheduler
from backend.services.system.permissions import get_system_permissions_report
from backend.services.system.platform_info import get_platform_information


def perform_system_health_check() -> dict[str, Any]:
    """Return comprehensive health status for the backend API, database, and services."""
    settings = get_settings()
    db_health = check_db_health()
    perms = get_system_permissions_report()
    platform_info = get_platform_information()
    ffmpeg_bin = resolve_ffmpeg_binary()

    return {
        "status": "healthy" if db_health.get("healthy") else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": db_health,
        "monitoring_running": monitor_scheduler.is_running,
        "websocket_clients": event_manager.active_connections_count,
        "capabilities": {
            "ffmpeg_available": ffmpeg_bin is not None,
            "ffmpeg_path": ffmpeg_bin,
            "nmap_available": perms.get("nmap_available", False),
            "npcap_installed": perms.get("npcap_installed", False),
            "is_admin": perms.get("is_admin", False),
        },
        "platform": platform_info,
    }

