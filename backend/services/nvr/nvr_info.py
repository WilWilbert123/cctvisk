"""Formats NVR ORM records into structured NVRResponse dictionaries."""

from __future__ import annotations

from typing import Any
from backend.models.nvr import NVR
from backend.utils.ip_utils import construct_safe_admin_url


def format_nvr_details(nvr: NVR) -> dict[str, Any]:
    """Serialize an NVR ORM instance and its parent Device into a response dictionary."""
    device = nvr.device
    http_port = nvr.http_port or 80
    admin_url = nvr.admin_url or construct_safe_admin_url(nvr.ip_address, http_port)
    return {
        "id": nvr.id,
        "device_id": nvr.device_id,
        "ip_address": nvr.ip_address,
        "mac_address": device.mac_address if device else None,
        "hostname": device.hostname if device else None,
        "label": device.label if device else None,
        "recorder_type": nvr.recorder_type or "NVR",
        "manufacturer": nvr.manufacturer or (device.manufacturer if device else None),
        "model": nvr.model or (device.model if device else None),
        "firmware_version": nvr.firmware_version,
        "serial_number": nvr.serial_number,
        "http_port": http_port,
        "rtsp_port": nvr.rtsp_port or 554,
        "sdk_port": nvr.sdk_port,
        "onvif_supported": nvr.onvif_supported,
        "detected_channels": nvr.detected_channels,
        "channels_info": list(nvr.channels_info or []),
        "admin_url": admin_url,
        "confidence": device.confidence if device else "MEDIUM",
        "classification_evidence": list(device.classification_evidence if device else []),
        "open_ports": list(device.open_ports if device else []),
        "is_online": bool(device.is_online if device else True),
        "notes": nvr.notes or (device.notes if device else None),
        "last_seen": device.last_seen if device else nvr.updated_at,
        "created_at": nvr.created_at,
        "updated_at": nvr.updated_at,
    }

