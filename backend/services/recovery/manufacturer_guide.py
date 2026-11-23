"""Loads official manufacturer recovery procedures from config/recovery_guides.json."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any
from backend.app.config import get_settings


@lru_cache
def load_all_recovery_guides() -> dict[str, dict[str, Any]]:
    """Load the catalog of manufacturer-specific password recovery workflows."""
    settings = get_settings()
    guides_file = settings.config_dir / "recovery_guides.json"
    if guides_file.exists():
        try:
            data = json.loads(guides_file.read_text(encoding="utf-8"))
            return data.get("manufacturers", {})
        except Exception:
            pass
    return {}


def match_manufacturer_guide(manufacturer_name: str | None) -> tuple[bool, dict[str, Any]]:
    """
    Find the matching manufacturer guide.
    Returns (is_verified_match, guide_dict).
    If manufacturer is unknown, returns (False, Generic guide) and flags manual identification.
    """
    guides = load_all_recovery_guides()
    if manufacturer_name and manufacturer_name.strip() and manufacturer_name.upper() != "UNKNOWN":
        lower_target = manufacturer_name.lower()
        for key, guide in guides.items():
            if key == "Generic":
                continue
            if key.lower() in lower_target or lower_target in guide.get("manufacturer", "").lower():
                return True, dict(guide)

    generic = guides.get(
        "Generic",
        {
            "manufacturer": "Unidentified / Generic ONVIF Manufacturer",
            "official_support_url": "https://www.onvif.org/",
            "official_tools": ["Manufacturer Config Utility"],
            "supports_reset_button": True,
            "supports_xml_export_recovery": False,
            "supports_qr_recovery": False,
            "summary": "Manufacturer not automatically verified. Please confirm the physical label on the camera/recorder.",
            "physical_reset_instructions": [],
            "authorized_workflow_steps": [],
            "warnings": [],
        },
    )
    return False, dict(generic)

