"""Verified NVR/DVR channel detection via ONVIF media profiles.

Never fabricates channel counts or recording statuses when unverified.
"""

from __future__ import annotations

from typing import Any
from backend.services.discovery.onvif_discovery import interrogate_onvif_device


async def detect_verified_nvr_channels(
    ip_address: str,
    onvif_port: int = 80,
    username: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """
    Query the recorder's ONVIF media service to retrieve verified media profiles/channels.
    If the recorder does not support ONVIF or requires credentials that were not provided,
    returns detected_channels=None with a clear explanation.
    """
    info = await interrogate_onvif_device(
        ip_address=ip_address,
        port=onvif_port,
        username=username,
        password=password,
    )
    profiles = info.get("media_profiles", [])
    if profiles:
        return {
            "verified": True,
            "detected_channels": len(profiles),
            "channels_info": profiles,
            "manufacturer": info.get("manufacturer"),
            "model": info.get("model"),
            "firmware_version": info.get("firmware_version"),
            "serial_number": info.get("serial_number"),
            "message": f"Retrieved {len(profiles)} verified media profile(s) via ONVIF.",
        }

    if info.get("auth_required"):
        return {
            "verified": False,
            "detected_channels": None,
            "channels_info": [],
            "auth_required": True,
            "message": (
                "Recorder requires authorized ONVIF credentials to enumerate video channels. "
                "Channel counts are not guessed without verification."
            ),
        }

    return {
        "verified": False,
        "detected_channels": None,
        "channels_info": [],
        "auth_required": False,
        "message": (
            "No ONVIF media profiles were returned by this recorder. "
            "Use the device's web administration interface to view proprietary channel configurations."
        ),
    }

