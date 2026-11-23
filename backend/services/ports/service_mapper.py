"""Maps open port numbers and banners to protocol names and service descriptions."""

from __future__ import annotations

from typing import Any
from backend.services.ports.common_ports import get_common_ports_metadata


def map_open_ports_to_services(open_ports: list[int]) -> list[dict[str, Any]]:
    """Return enriched service descriptions for each open port."""
    catalog = {int(item["port"]): item for item in get_common_ports_metadata()}
    mapped: list[dict[str, Any]] = []
    for port in sorted(set(open_ports)):
        if port in catalog:
            mapped.append(dict(catalog[port]))
        else:
            mapped.append(
                {
                    "port": port,
                    "protocol": "TCP",
                    "service": f"TCP/{port}",
                    "description": "Custom or uncataloged network service",
                    "category_relevance": [],
                }
            )
    return mapped


def infer_protocols_from_ports(open_ports: list[int], onvif_available: bool = False) -> list[str]:
    """Derive protocol identifiers from verified open ports."""
    protocols: set[str] = set()
    port_set = set(open_ports)
    if 80 in port_set or 8080 in port_set or 8000 in port_set:
        protocols.add("HTTP")
    if 443 in port_set or 8443 in port_set:
        protocols.add("HTTPS")
    if 554 in port_set or 8554 in port_set:
        protocols.add("RTSP")
    if onvif_available or 3702 in port_set or 8899 in port_set:
        protocols.add("ONVIF")
    if 37777 in port_set:
        protocols.add("DAHUA-SDK")
    if 8000 in port_set:
        protocols.add("HIKVISION-SDK")
    if 9000 in port_set:
        protocols.add("REOLINK-MEDIA")
    if 34567 in port_set:
        protocols.add("XMEYE-DVR")
    if 53 in port_set:
        protocols.add("DNS")
    if 631 in port_set or 9100 in port_set:
        protocols.add("IPP/PRINT")
    if 445 in port_set:
        protocols.add("SMB")
    return sorted(protocols)

