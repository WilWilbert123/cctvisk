"""Reverse DNS and local hostname resolution."""

from __future__ import annotations

import asyncio
import socket
from backend.utils.ip_utils import validate_authorized_ip


async def resolve_hostname(ip_address: str, timeout_seconds: float = 1.0) -> str | None:
    """Resolve the reverse DNS / NetBIOS hostname for a local IP address without blocking."""
    valid_ip = validate_authorized_ip(ip_address)
    try:
        host_info = await asyncio.wait_for(
            asyncio.to_thread(socket.gethostbyaddr, valid_ip),
            timeout=timeout_seconds,
        )
        hostname = host_info[0]
        if hostname and hostname != valid_ip:
            return hostname
    except Exception:
        pass
    return None

