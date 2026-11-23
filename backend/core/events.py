"""WebSocket connection manager and asynchronous event bus."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from fastapi import WebSocket
from backend.core.logging import get_logger

logger = get_logger("events")


class EventManager:
    """Manages active WebSocket clients and broadcasts real-time system events."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._recent_events: list[dict[str, Any]] = []
        self._max_recent = 100

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WebSocket client connected (total=%d)", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WebSocket client disconnected (total=%d)", len(self._connections))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast a structured event to all connected WebSocket clients."""
        payload = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        self._recent_events.insert(0, payload)
        if len(self._recent_events) > self._max_recent:
            self._recent_events = self._recent_events[: self._max_recent]

        async with self._lock:
            clients = list(self._connections)

        stale: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)

        if stale:
            async with self._lock:
                for ws in stale:
                    self._connections.discard(ws)

    def broadcast_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """Fire-and-forget broadcast from synchronous or background contexts."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(event_type, data))
        except RuntimeError:
            payload = {
                "type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }
            self._recent_events.insert(0, payload)
            if len(self._recent_events) > self._max_recent:
                self._recent_events = self._recent_events[: self._max_recent]

    def get_recent_events(self, limit: int = 30) -> list[dict[str, Any]]:
        return self._recent_events[:limit]

    @property
    def active_connections_count(self) -> int:
        return len(self._connections)


event_manager = EventManager()

