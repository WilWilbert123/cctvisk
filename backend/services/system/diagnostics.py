"""Cross-platform firewall, LAN access, and Android PWA connection diagnostics."""

from __future__ import annotations

from typing import Any
from backend.app.config import get_settings
from backend.services.network.interface import get_active_interface
from backend.services.system.health_check import perform_system_health_check
from backend.services.system.permissions import get_system_permissions_report


def get_full_system_diagnostics() -> dict[str, Any]:
    """Return complete diagnostics including Windows/macOS firewall and Android LAN instructions."""
    settings = get_settings()
    health = perform_system_health_check()
    perms = get_system_permissions_report()
    active_iface = get_active_interface()
    lan_ip = active_iface.get("ip_address", "127.0.0.1")

    return {
        "health": health,
        "permissions": perms,
        "network_interface": active_iface,
        "lan_access": {
            "enabled": settings.ALLOW_LAN_ACCESS,
            "host_binding": settings.HOST,
            "port": settings.PORT,
            "lan_ip": lan_ip,
            "backend_lan_url": f"http://{lan_ip}:{settings.PORT}",
            "frontend_dev_lan_url": f"http://{lan_ip}:5173",
            "pairing_token": settings.API_ACCESS_TOKEN,
            "android_instructions": [
                "Connect your Android phone or tablet to the same Wi-Fi network as this host computer.",
                f"Ensure ALLOW_LAN_ACCESS=true is set in .env and open http://{lan_ip}:5173 (dev) or http://{lan_ip}:{settings.PORT} (production) in Chrome on Android.",
                "Enter the Local API Pairing Token shown in Settings -> Security when prompted.",
                "Tap 'Install App' / 'Add to Home screen' in Chrome on Android to install the responsive PWA.",
                "Note: All low-level ARP, ONVIF multicast, and RTSP transcoding operations execute on this host computer.",
            ],
            "windows_firewall_command": (
                f'New-NetFirewallRule -DisplayName "CCTV Assistant LAN" -Direction Inbound '
                f"-LocalPort {settings.PORT},5173 -Protocol TCP -Action Allow -Profile Private"
            ),
            "macos_firewall_note": (
                "System Settings -> Network -> Firewall -> Options -> Allow incoming connections for Python / Node on private LAN."
            ),
        },
    }

