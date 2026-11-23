"""MAC address normalization and OUI prefix extraction utilities."""

from __future__ import annotations

import re

MAC_REGEX = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$"
)


def normalize_mac(mac: str | None) -> str | None:
    """
    Normalize a MAC address to uppercase colon-separated format (XX:XX:XX:XX:XX:XX).
    Returns None if invalid or broadcast/unspecified.
    """
    if not mac:
        return None
    cleaned = mac.strip().upper()
    hex_only = re.sub(r"[^0-9A-F]", "", cleaned)
    if len(hex_only) != 12:
        # Handle Windows ARP format where leading zeros in octets might be omitted (e.g., 0-1a-2b-3c-4d-5e)
        parts = re.split(r"[:-]", cleaned)
        if len(parts) == 6 and all(1 <= len(p) <= 2 and all(c in "0123456789ABCDEF" for c in p) for p in parts):
            hex_only = "".join(p.zfill(2) for p in parts)
        else:
            return None

    formatted = ":".join(hex_only[i : i + 2] for i in range(0, 12, 2))
    if formatted in {"FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00"}:
        return None
    return formatted


def extract_oui(mac: str | None) -> str | None:
    """Return the 3-octet OUI prefix (XX:XX:XX) from a MAC address."""
    normalized = normalize_mac(mac)
    if not normalized:
        return None
    return normalized[:8]

