"""Builds step-by-step authorized password recovery workflow for a target device."""

from __future__ import annotations

from typing import Any
from backend.models.device import Device
from backend.services.recovery.manufacturer_guide import match_manufacturer_guide


def build_recovery_workflow_for_device(
    device: Device, manual_manufacturer: str | None = None
) -> dict[str, Any]:
    """Assemble the complete authorized recovery workflow for a discovered camera or recorder."""
    mfg = manual_manufacturer or device.manufacturer
    model = device.model
    if device.camera:
        mfg = mfg or device.camera.manufacturer
        model = model or device.camera.model
    elif device.nvr:
        mfg = mfg or device.nvr.manufacturer
        model = model or device.nvr.model

    verified, guide = match_manufacturer_guide(mfg)
    return {
        "device_id": device.id,
        "ip_address": device.ip_address,
        "detected_manufacturer": mfg,
        "detected_model": model,
        "manufacturer_verified": verified,
        "requires_manual_identification": not verified,
        "guide": guide,
    }

