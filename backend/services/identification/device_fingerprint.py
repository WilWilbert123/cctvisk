"""Combines all discovery signals into a structured device fingerprint."""

from __future__ import annotations

from typing import Any
from backend.services.identification.hostname import resolve_hostname
from backend.services.identification.mac_lookup import lookup_mac_vendor
from backend.services.identification.manufacturer import identify_manufacturer
from backend.services.identification.service_detection import inspect_device_services


async def build_device_fingerprint(
    ip_address: str,
    mac_address: str | None = None,
    open_ports: list[int] | None = None,
    onvif_info: dict[str, Any] | None = None,
    mdns_info: dict[str, Any] | None = None,
    ssdp_info: dict[str, Any] | None = None,
    is_gateway: bool = False,
    is_host: bool = False,
) -> dict[str, Any]:
    """Gather hostname, OUI vendor, HTTP/RTSP service banners, and protocol metadata."""
    ports = sorted(set(open_ports or []))
    hostname = await resolve_hostname(ip_address)
    service_info = await inspect_device_services(ip_address, ports)
    mac_vendor = lookup_mac_vendor(mac_address)

    onvif_mfg = (onvif_info or {}).get("manufacturer")
    mfg_result = identify_manufacturer(
        mac_address=mac_address,
        onvif_manufacturer=onvif_mfg,
        banners=service_info.get("banners"),
        hostname=hostname,
        mdns_info=mdns_info,
        ssdp_info=ssdp_info,
    )

    return {
        "ip_address": ip_address,
        "mac_address": mac_address,
        "hostname": hostname or (mdns_info or {}).get("hostname"),
        "mac_vendor": mac_vendor,
        "manufacturer": mfg_result.get("manufacturer"),
        "is_cctv_vendor": mfg_result.get("is_cctv_vendor", False),
        "manufacturer_evidence": mfg_result.get("evidence", []),
        "open_ports": ports,
        "banners": service_info.get("banners", {}),
        "rtsp_verified": service_info.get("rtsp_verified", False),
        "onvif_info": onvif_info or {},
        "mdns_info": mdns_info or {},
        "ssdp_info": ssdp_info or {},
        "is_gateway": is_gateway,
        "is_host": is_host,
    }
