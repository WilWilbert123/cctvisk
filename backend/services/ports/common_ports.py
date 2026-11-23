"""Loads and exposes the documented list of common CCTV and network service ports."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any
from backend.app.config import get_settings
from backend.core.constants import DEFAULT_COMMON_PORTS


@lru_cache
def get_common_ports_metadata() -> list[dict[str, Any]]:
    """Load common port definitions from config/common_ports.json."""
    settings = get_settings()
    ports_file = settings.config_dir / "common_ports.json"
    if ports_file.exists():
        try:
            data = json.loads(ports_file.read_text(encoding="utf-8"))
            return data.get("ports", [])
        except Exception:
            pass
    return [{"port": p, "protocol": "TCP", "service": f"PORT-{p}", "description": ""} for p in DEFAULT_COMMON_PORTS]


def get_default_scan_ports() -> list[int]:
    """Return sorted list of default TCP ports to check on discovered LAN devices."""
    meta = get_common_ports_metadata()
    tcp_ports = [int(item["port"]) for item in meta if item.get("protocol", "TCP").upper() == "TCP"]
    return sorted(set(tcp_ports or DEFAULT_COMMON_PORTS))

