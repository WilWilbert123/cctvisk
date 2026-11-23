"""NVR and DVR detection and metadata extraction."""

from __future__ import annotations

from typing import Any
from backend.utils.ip_utils import construct_safe_admin_url


def extract_nvr_candidate_attributes(
    ip_address: str,
    classification: dict[str, Any],
    fingerprint: dict[str, Any],
) -> dict[str, Any] | None:
    """
    If a classified device is an NVR or DVR, build its NVR persistence attributes.
    Never invents channel counts; only populates detected_channels when ONVIF media profiles confirm them.
    """
    category = classification.get("category")
    if category not in ("NVR", "DVR"):
        return None

    open_ports: list[int] = fingerprint.get("open_ports", [])
    port_set = set(open_ports)
    onvif_info: dict[str, Any] = fingerprint.get("onvif_info") or {}

    http_port = 80 if 80 in port_set else (8080 if 8080 in port_set else 80)
    rtsp_port = 554 if 554 in port_set else 554
    sdk_port = None
    for candidate_sdk in (8000, 37777, 34567, 9000):
        if candidate_sdk in port_set:
            sdk_port = candidate_sdk
            break

    profiles = onvif_info.get("media_profiles", [])
    detected_channels = len(profiles) if profiles else None

    return {
        "ip_address": ip_address,
        "recorder_type": category,
        "manufacturer": classification.get("manufacturer"),
        "model": classification.get("model"),
        "firmware_version": onvif_info.get("firmware_version"),
        "serial_number": onvif_info.get("serial_number"),
        "http_port": http_port,
        "rtsp_port": rtsp_port,
        "sdk_port": sdk_port,
        "onvif_supported": bool(classification.get("onvif_available", False)),
        "detected_channels": detected_channels,
        "channels_info": profiles,
        "admin_url": construct_safe_admin_url(ip_address, http_port),
    }

