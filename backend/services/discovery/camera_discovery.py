"""Specialized camera metadata extraction from discovery signals."""

from __future__ import annotations

import json
from typing import Any
from backend.app.config import get_settings
from backend.utils.ip_utils import construct_safe_admin_url


def _get_default_rtsp_path_for_vendor(manufacturer: str | None) -> str:
    if not manufacturer:
        return "/Streaming/Channels/101"
    settings = get_settings()
    mfg_file = settings.config_dir / "manufacturers.json"
    if mfg_file.exists():
        try:
            data = json.loads(mfg_file.read_text(encoding="utf-8"))
            templates = data.get("rtsp_templates", {})
            for key, paths in templates.items():
                if key.lower() in manufacturer.lower() and paths:
                    return paths[0]
        except Exception:
            pass
    return "/Streaming/Channels/101"


def extract_camera_candidate_attributes(
    ip_address: str,
    classification: dict[str, Any],
    fingerprint: dict[str, Any],
) -> dict[str, Any] | None:
    """
    If a classified device is a CAMERA or ONVIF_CAMERA, build its Camera persistence attributes.
    Returns None if the device is not a camera.
    """
    category = classification.get("category")
    if category not in ("CAMERA", "ONVIF_CAMERA", "NVR", "DVR"):
        return None

    open_ports: list[int] = fingerprint.get("open_ports", [])
    port_set = set(open_ports)
    onvif_info: dict[str, Any] = fingerprint.get("onvif_info") or {}
    manufacturer = classification.get("manufacturer")
    model = classification.get("model")

    http_port = 80
    for p in (80, 8080, 8000):
        if p in port_set:
            http_port = p
            break
    https_port = 443 if 443 in port_set else (8443 if 8443 in port_set else None)
    rtsp_port = 554 if 554 in port_set else (8554 if 8554 in port_set else 554)
    onvif_port = int(onvif_info.get("onvif_port") or onvif_info.get("port") or (8899 if 8899 in port_set else http_port))

    profiles = onvif_info.get("media_profiles", [])
    rtsp_path = _get_default_rtsp_path_for_vendor(manufacturer)
    if profiles and profiles[0].get("stream_uri"):
        from urllib.parse import urlparse
        try:
            parsed = urlparse(profiles[0]["stream_uri"])
            if parsed.path:
                rtsp_path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        except Exception:
            pass

    return {
        "ip_address": ip_address,
        "manufacturer": manufacturer,
        "model": model,
        "firmware_version": onvif_info.get("firmware_version"),
        "serial_number": onvif_info.get("serial_number"),
        "hardware_id": onvif_info.get("hardware_id"),
        "onvif_supported": bool(classification.get("onvif_available", False)),
        "onvif_port": onvif_port,
        "onvif_xaddrs": onvif_info.get("xaddrs", []),
        "onvif_scopes": onvif_info.get("scopes", []),
        "onvif_capabilities": onvif_info.get("capabilities", {}),
        "media_profiles": profiles,
        "rtsp_available": bool(classification.get("rtsp_available", False) or (554 in port_set)),
        "rtsp_port": rtsp_port,
        "rtsp_path": rtsp_path,
        "http_port": http_port,
        "https_port": https_port,
        "admin_url": construct_safe_admin_url(ip_address, https_port or http_port, use_https=bool(https_port)),
        "requires_auth": bool(onvif_info.get("auth_required", True)),
    }

