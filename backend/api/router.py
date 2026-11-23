"""Main API v1 router aggregating all domain routers and the real-time WebSocket endpoint."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.api.routes import (
    cameras,
    dashboard,
    devices,
    discovery,
    history,
    monitoring,
    network,
    nvr,
    onvif,
    ports,
    recovery,
    settings,
    system,
)
from backend.core.constants import API_V1_PREFIX
from backend.core.events import event_manager

api_router = APIRouter(prefix=API_V1_PREFIX)

api_router.include_router(dashboard.router)
api_router.include_router(network.router)
api_router.include_router(devices.router)
api_router.include_router(cameras.router)
api_router.include_router(nvr.router)
api_router.include_router(discovery.router)
api_router.include_router(ports.router)
api_router.include_router(onvif.router)
api_router.include_router(monitoring.router)
api_router.include_router(recovery.router)
api_router.include_router(history.router)
api_router.include_router(settings.router)
api_router.include_router(system.router)


@api_router.websocket("/ws")
async def api_v1_websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time WebSocket event channel under /api/v1/ws."""
    await event_manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await event_manager.disconnect(websocket)
    except Exception:
        await event_manager.disconnect(websocket)

