"""Reverse DNS and local hostname resolution."""

from __future__ import annotations

import asyncio
import re
import socket
import subprocess
from backend.utils.ip_utils import validate_authorized_ip


def _resolve_from_arp_cache(ip_address: str) -> str | None:
    """Fallback to parsing the hostname from `arp -a` on macOS/Linux."""
    try:
        proc = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        out = proc.stdout or ""
        # Format on macOS: "rap2200f-f9f078.lan (192.168.110.10) at 30:d:9e:f9:f0:78 on en0"
        pattern = re.compile(
            r"^\s*([^\s(?]+)\s+\(" + re.escape(ip_address) + r"\)",
            re.MULTILINE,
        )
        m = pattern.search(out)
        if m:
            candidate = m.group(1).strip()
            if candidate and candidate != "?" and candidate != ip_address:
                return candidate
    except Exception:
        pass
    return None


async def resolve_hostname(ip_address: str, timeout_seconds: float = 1.0) -> str | None:
    """Resolve the reverse DNS / NetBIOS / ARP hostname for a local IP address without blocking."""
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
    return await asyncio.to_thread(_resolve_from_arp_cache, valid_ip)

