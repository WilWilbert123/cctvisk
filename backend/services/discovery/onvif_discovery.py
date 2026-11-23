"""High-level ONVIF discovery and device interrogation coordinator."""

from __future__ import annotations

from typing import Any
from backend.services.onvif.capabilities import fetch_onvif_capabilities
from backend.services.onvif.device_information import fetch_onvif_device_information
from backend.services.onvif.discovery import discover_onvif_devices
from backend.services.onvif.media_profiles import fetch_onvif_media_profiles_and_streams


async def interrogate_onvif_device(
    ip_address: str,
    port: int = 80,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """Query ONVIF device information, capabilities, and media profiles on a target IP."""
    dev_info = await fetch_onvif_device_information(
        ip_address=ip_address, port=port, username=username, password=password
    )
    caps = await fetch_onvif_capabilities(
        ip_address=ip_address, port=port, username=username, password=password
    )
    media_xaddr = caps.get("media")
    profiles = await fetch_onvif_media_profiles_and_streams(
        ip_address=ip_address,
        port=port,
        media_xaddr=media_xaddr,
        username=username,
        password=password,
    )

    reachable = bool(dev_info.get("ok") or caps or profiles or dev_info.get("auth_required"))
    return {
        "ip_address": ip_address,
        "port": port,
        "reachable": reachable,
        "authenticated": bool(dev_info.get("ok")),
        "auth_required": bool(dev_info.get("auth_required", False)),
        "manufacturer": dev_info.get("manufacturer"),
        "model": dev_info.get("model"),
        "firmware_version": dev_info.get("firmware_version"),
        "serial_number": dev_info.get("serial_number"),
        "hardware_id": dev_info.get("hardware_id"),
        "capabilities": caps,
        "media_profiles": profiles,
        "error": dev_info.get("error") if not reachable else None,
    }


async def run_onvif_discovery_with_enrichment(timeout_seconds: float = 2.5) -> list[dict[str, Any]]:
    """Run UDP multicast ONVIF WS-Discovery and enrich discovered endpoints with unauthenticated SOAP metadata."""
    items = await discover_onvif_devices(timeout_seconds=timeout_seconds)
    enriched: list[dict[str, Any]] = []
    for item in items:
        ip_addr = item["ip_address"]
        port = int(item.get("onvif_port") or 80)
        soap_info = await interrogate_onvif_device(ip_addr, port=port)
        merged = dict(item)
        if soap_info.get("manufacturer"):
            merged["manufacturer"] = soap_info["manufacturer"]
        if soap_info.get("model"):
            merged["model"] = soap_info["model"]
        merged["firmware_version"] = soap_info.get("firmware_version")
        merged["serial_number"] = soap_info.get("serial_number")
        merged["hardware_id"] = soap_info.get("hardware_id")
        merged["capabilities"] = soap_info.get("capabilities", {})
        merged["media_profiles"] = soap_info.get("media_profiles", [])
        merged["auth_required"] = soap_info.get("auth_required", True)
        enriched.append(merged)
    return enriched

