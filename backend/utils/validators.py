"""Input validators for user-supplied parameters."""

from __future__ import annotations

import re
from backend.utils.ip_utils import validate_authorized_ip, validate_authorized_subnet
from backend.utils.mac_utils import normalize_mac

SAFE_LABEL_PATTERN = re.compile(r"^[\w\s\-\.\(\)\[\]/:#@]{1,120}$")


def validate_port(port: int) -> int:
    """Ensure a port number is within 1..65535."""
    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise ValueError(f"Port must be an integer between 1 and 65535 (got {port}).")
    return port


def validate_port_list(ports: list[int] | None) -> list[int]:
    """Validate and deduplicate a list of TCP/UDP ports."""
    if not ports:
        return []
    if len(ports) > 100:
        raise ValueError("Cannot scan more than 100 ports in a single request.")
    return sorted({validate_port(int(p)) for p in ports})


def sanitize_text(value: str | None, max_length: int = 500) -> str | None:
    """Strip control characters and enforce maximum string length."""
    if value is None:
        return None
    cleaned = "".join(ch for ch in value if ch == "\n" or ch == "\t" or ord(ch) >= 32).strip()
    return cleaned[:max_length]


__all__ = [
    "validate_authorized_ip",
    "validate_authorized_subnet",
    "normalize_mac",
    "validate_port",
    "validate_port_list",
    "sanitize_text",
]

