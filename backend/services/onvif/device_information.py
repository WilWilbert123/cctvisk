"""ONVIF GetDeviceInformation operation."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from backend.services.onvif.connection import send_onvif_soap_request


def parse_device_information_xml(xml_text: str) -> dict[str, str | None]:
    """Extract Manufacturer, Model, FirmwareVersion, SerialNumber, HardwareId from SOAP XML."""
    info: dict[str, str | None] = {
        "manufacturer": None,
        "model": None,
        "firmware_version": None,
        "serial_number": None,
        "hardware_id": None,
    }
    if not xml_text:
        return info
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return info

    tag_map = {
        "Manufacturer": "manufacturer",
        "Model": "model",
        "FirmwareVersion": "firmware_version",
        "SerialNumber": "serial_number",
        "HardwareId": "hardware_id",
    }
    for elem in root.iter():
        local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local_name in tag_map and elem.text:
            info[tag_map[local_name]] = elem.text.strip()
    return info


async def fetch_onvif_device_information(
    ip_address: str,
    port: int = 80,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """Query /onvif/device_service for GetDeviceInformation."""
    res = await send_onvif_soap_request(
        ip_address=ip_address,
        port=port,
        service_path="/onvif/device_service",
        body_xml="<tds:GetDeviceInformation/>",
        username=username,
        password=password,
    )
    if not res.get("ok"):
        return {
            "ok": False,
            "auth_required": res.get("auth_required", False),
            "error": res.get("error"),
        }
    parsed = parse_device_information_xml(res.get("xml", ""))
    return {
        "ok": True,
        "auth_required": False,
        **parsed,
    }

