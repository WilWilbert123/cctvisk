"""Recorder online/offline and service port status verification."""

from __future__ import annotations

from typing import Any
from backend.services.network.ping import check_host_reachable


async def check_recorder_status(
    ip_address: str, http_port: int = 80, rtsp_port: int = 554, sdk_port: int | None = None
) -> dict[str, Any]:
    """Check whether an NVR/DVR is online and verify its web, RTSP, and SDK control ports."""
    is_online, latency_ms, open_ports, method = await check_host_reachable(
        ip_address, timeout_ms=800, enable_icmp=True
    )
    port_set = set(open_ports)
    return {
        "ip_address": ip_address,
        "is_online": is_online,
        "latency_ms": latency_ms,
        "open_ports": open_ports,
        "probe_method": method,
        "web_available": http_port in port_set,
        "rtsp_available": rtsp_port in port_set,
        "sdk_available": bool(sdk_port and sdk_port in port_set),
    }

