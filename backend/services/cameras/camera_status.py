"""Real-time camera availability and RTSP/HTTP service status verification."""

from __future__ import annotations

from typing import Any
from backend.services.identification.service_detection import probe_rtsp_options
from backend.services.network.ping import check_host_reachable


async def check_camera_live_status(
    ip_address: str, rtsp_port: int = 554, http_port: int = 80
) -> dict[str, Any]:
    """Check whether a camera is online and whether its RTSP and HTTP ports respond."""
    is_online, latency_ms, open_ports, method = await check_host_reachable(
        ip_address, timeout_ms=800, enable_icmp=True
    )
    rtsp_info = await probe_rtsp_options(ip_address, port=rtsp_port, timeout=1.2)
    return {
        "ip_address": ip_address,
        "is_online": is_online or rtsp_info.get("is_rtsp", False),
        "latency_ms": latency_ms,
        "open_ports": open_ports,
        "probe_method": method,
        "rtsp_responding": bool(rtsp_info.get("is_rtsp", False)),
        "rtsp_requires_auth": bool(rtsp_info.get("requires_auth", False)),
        "rtsp_server": rtsp_info.get("server"),
        "http_responding": http_port in open_ports,
    }

