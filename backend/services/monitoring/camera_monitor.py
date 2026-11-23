"""Specialized camera availability check verifying RTSP/HTTP ports in addition to host liveness."""

from __future__ import annotations

from typing import Any
from backend.models.camera import Camera
from backend.services.cameras.camera_status import check_camera_live_status


async def check_monitored_camera(camera: Camera) -> dict[str, Any]:
    """Verify both network reachability and RTSP/HTTP responsiveness for a Camera."""
    return await check_camera_live_status(
        ip_address=camera.ip_address,
        rtsp_port=camera.rtsp_port or 554,
        http_port=camera.http_port or 80,
    )

