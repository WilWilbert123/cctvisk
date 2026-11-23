"""Event worker helper for broadcasting and persisting system notifications."""

from __future__ import annotations

from typing import Any
from backend.core.events import event_manager
from backend.database.session import session_scope
from backend.repositories.scan_repository import ScanRepository


async def emit_and_log_event(
    event_type: str,
    title: str,
    message: str,
    level: str = "info",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Persist an ActivityLog entry in SQLite and broadcast it over WebSockets."""
    with session_scope() as session:
        repo = ScanRepository(session)
        repo.log_activity(
            event_type=event_type,
            title=title,
            message=message,
            level=level,
            metadata_json=metadata or {},
        )
    await event_manager.broadcast(
        "system_notification",
        {
            "level": level,
            "title": title,
            "message": message,
            "metadata": metadata or {},
        },
    )

