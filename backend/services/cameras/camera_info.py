"""Formats Camera ORM models into rich CameraResponse dictionaries."""

from __future__ import annotations

from typing import Any
from backend.models.camera import Camera
from backend.services.cameras.camera_protocols import build_authenticated_rtsp_url
from backend.utils.ip_utils import construct_safe_admin_url, mask_rtsp_url


def format_camera_details(
    camera: Camera,
    has_saved_credentials: bool = False,
    saved_username: str | None = None,
    stream_active: bool = False,
) -> dict[str, Any]:
    """Serialize a Camera ORM entity and its parent Device into a complete dictionary."""
    device = camera.device
    open_ports = list(device.open_ports if device else [])
    rtsp_path = camera.rtsp_path or "/Streaming/Channels/101"
    raw_rtsp = build_authenticated_rtsp_url(
        ip_address=camera.ip_address,
        rtsp_port=camera.rtsp_port or 554,
        stream_path=rtsp_path,
        username=saved_username,
        password="***" if saved_username else None,
    )
    admin_url = camera.admin_url or construct_safe_admin_url(
        camera.ip_address,
        camera.https_port or camera.http_port or 80,
        use_https=bool(camera.https_port),
    )

    return {
        "id": camera.id,
        "device_id": camera.device_id,
        "ip_address": camera.ip_address,
        "mac_address": device.mac_address if device else None,
        "hostname": device.hostname if device else None,
        "label": device.label if device else None,
        "manufacturer": camera.manufacturer or (device.manufacturer if device else None),
        "model": camera.model or (device.model if device else None),
        "firmware_version": camera.firmware_version,
        "serial_number": camera.serial_number,
        "hardware_id": camera.hardware_id,
        "confidence": device.confidence if device else "MEDIUM",
        "classification_evidence": list(device.classification_evidence if device else []),
        "open_ports": open_ports,
        "detected_protocols": list(device.detected_protocols if device else []),
        "onvif_supported": camera.onvif_supported,
        "onvif_port": camera.onvif_port,
        "onvif_xaddrs": list(camera.onvif_xaddrs or []),
        "onvif_scopes": list(camera.onvif_scopes or []),
        "onvif_capabilities": dict(camera.onvif_capabilities or {}),
        "media_profiles": list(camera.media_profiles or []),
        "rtsp_available": camera.rtsp_available or (554 in open_ports),
        "rtsp_port": camera.rtsp_port,
        "rtsp_path": rtsp_path,
        "rtsp_url_masked": mask_rtsp_url(raw_rtsp),
        "http_port": camera.http_port,
        "https_port": camera.https_port,
        "snapshot_path": camera.snapshot_path,
        "admin_url": admin_url,
        "requires_auth": camera.requires_auth,
        "is_online": bool(device.is_online if device else True),
        "is_favorite": bool(device.is_favorite if device else False),
        "notes": device.notes if device else camera.stream_notes,
        "has_saved_credentials": has_saved_credentials,
        "saved_username": saved_username,
        "stream_active": stream_active,
        "last_seen": device.last_seen if device else camera.updated_at,
        "created_at": camera.created_at,
        "updated_at": camera.updated_at,
    }

