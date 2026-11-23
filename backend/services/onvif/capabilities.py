"""ONVIF GetCapabilities and GetServices retrieval."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from backend.services.onvif.connection import send_onvif_soap_request


def parse_capabilities_xml(xml_text: str) -> dict[str, Any]:
    """Extract Analytics, Device, Events, Imaging, Media, and PTZ XAddr capabilities."""
    caps: dict[str, Any] = {}
    if not xml_text:
        return caps
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return caps

    sections = ("Analytics", "Device", "Events", "Imaging", "Media", "PTZ")
    for elem in root.iter():
        local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local_name in sections:
            for child in elem:
                child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if child_name == "XAddr" and child.text:
                    caps[local_name.lower()] = child.text.strip()
    return caps


async def fetch_onvif_capabilities(
    ip_address: str,
    port: int = 80,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """Query GetCapabilities on /onvif/device_service."""
    res = await send_onvif_soap_request(
        ip_address=ip_address,
        port=port,
        service_path="/onvif/device_service",
        body_xml="<tds:GetCapabilities><tds:Category>All</tds:Category></tds:GetCapabilities>",
        username=username,
        password=password,
    )
    if not res.get("ok"):
        return {}
    return parse_capabilities_xml(res.get("xml", ""))

