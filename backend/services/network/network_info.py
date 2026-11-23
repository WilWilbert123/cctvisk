"""Aggregates active network interface, subnet, DNS, and permission details."""

from __future__ import annotations

from typing import Any
from backend.app.config import get_settings
from backend.core.permissions import get_permission_summary
from backend.services.network.interface import get_active_interface, list_network_interfaces


def get_full_network_info(preferred_interface: str | None = None) -> dict[str, Any]:
    """Return complete real-time local network status and host capabilities."""
    settings = get_settings()
    active = get_active_interface(preferred_interface)
    all_interfaces = list_network_interfaces()
    permissions = get_permission_summary()

    lan_url = (
        f"http://{active['ip_address']}:{settings.PORT}"
        if active.get("is_up") and active.get("ip_address") != "127.0.0.1"
        else f"http://localhost:{settings.PORT}"
    )

    return {
        "interface_name": active["interface_name"],
        "ip_address": active["ip_address"],
        "netmask": active["netmask"],
        "subnet_cidr": active["subnet_cidr"],
        "gateway": active.get("gateway"),
        "mac_address": active.get("mac_address"),
        "is_connected": active.get("is_up", False),
        "connection_type": active.get("connection_type", "Ethernet/Wi-Fi"),
        "ssid": active.get("ssid"),
        "speed_mbps": active.get("speed_mbps"),
        "interfaces": all_interfaces,
        "lan_dashboard_url": lan_url,
        "allow_lan_access": settings.ALLOW_LAN_ACCESS,
        "permissions": permissions,
    }

