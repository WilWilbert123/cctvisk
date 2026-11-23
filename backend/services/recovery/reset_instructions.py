"""Formats physical hardware reset-button instructions and warnings per vendor/model."""

from __future__ import annotations

from typing import Any
from backend.services.recovery.manufacturer_guide import match_manufacturer_guide


def get_reset_instructions_for_device(
    manufacturer: str | None, model: str | None = None
) -> dict[str, Any]:
    """Return physical reset instructions, official support URL, and model notes."""
    verified, guide = match_manufacturer_guide(manufacturer)
    return {
        "manufacturer_verified": verified,
        "detected_manufacturer": manufacturer,
        "detected_model": model,
        "supports_reset_button": bool(guide.get("supports_reset_button", True)),
        "physical_reset_instructions": list(guide.get("physical_reset_instructions", [])),
        "warnings": list(guide.get("warnings", [])),
        "official_support_url": guide.get("official_support_url"),
    }

