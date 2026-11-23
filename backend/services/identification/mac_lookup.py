"""Local OUI database lookup for MAC address vendor resolution (with IEEE Scapy MANUFDB fallback)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any
from backend.app.config import get_settings
from backend.utils.mac_utils import extract_oui, normalize_mac

try:
    from scapy.data import MANUFDB as _SCAPY_MANUFDB
except Exception:
    _SCAPY_MANUFDB = None

CCTV_VENDOR_KEYWORDS = (
    "hikvision",
    "dahua",
    "axis communications",
    "reolink",
    "vivotek",
    "uniview",
    "hanwha",
    "bosch security",
    "amcrest",
    "pelco",
    "avigilon",
    "mobotix",
    "tiandy",
    "xiongmai",
    "ezviz",
)

PRINTER_VENDOR_KEYWORDS = (
    "brother",
    "seiko epson",
    "canon",
    "ricoh",
    "lexmark",
    "kyocera",
    "konica minolta",
    "xerox",
    "zebra technologies",
)

COMPUTER_VENDOR_KEYWORDS = (
    "asustek",
    "dell",
    "intel corporate",
    "hewlett packard",
    "lenovo",
    "gigabyte",
    "micro-star",
    "qnap",
    "synology",
    "acer",
)


@lru_cache
def _load_oui_database() -> dict[str, dict[str, Any]]:
    settings = get_settings()
    mfg_file = settings.config_dir / "manufacturers.json"
    if mfg_file.exists():
        try:
            data = json.loads(mfg_file.read_text(encoding="utf-8"))
            return data.get("oui_database", {})
        except Exception:
            pass
    return {}


def lookup_mac_vendor(mac_address: str | None) -> dict[str, Any]:
    """
    Look up a MAC address against the maintained local OUI database and IEEE MANUFDB.
    Never invents a manufacturer if the OUI prefix is not recognized.
    """
    oui = extract_oui(mac_address)
    if not oui:
        return {
            "oui": None,
            "manufacturer": None,
            "category_hint": "UNKNOWN",
            "is_cctv_vendor": False,
        }

    db = _load_oui_database()
    match = db.get(oui.upper())
    if match:
        return {
            "oui": oui,
            "manufacturer": match.get("manufacturer"),
            "category_hint": match.get("category_hint", "UNKNOWN"),
            "is_cctv_vendor": bool(match.get("is_cctv_vendor", False)),
        }

    norm = normalize_mac(mac_address)
    if norm and _SCAPY_MANUFDB is not None:
        try:
            ieee_mfg = _SCAPY_MANUFDB._get_manuf(norm)
            if ieee_mfg and ieee_mfg.upper() != norm.upper() and ":" not in ieee_mfg:
                lower_mfg = ieee_mfg.lower()
                is_cctv = any(k in lower_mfg for k in CCTV_VENDOR_KEYWORDS)
                cat_hint = "UNKNOWN"
                if is_cctv:
                    cat_hint = "CAMERA"
                elif any(k in lower_mfg for k in PRINTER_VENDOR_KEYWORDS):
                    cat_hint = "PRINTER"
                elif any(k in lower_mfg for k in COMPUTER_VENDOR_KEYWORDS):
                    cat_hint = "COMPUTER"
                return {
                    "oui": oui,
                    "manufacturer": ieee_mfg,
                    "category_hint": cat_hint,
                    "is_cctv_vendor": is_cctv,
                }
        except Exception:
            pass

    return {
        "oui": oui,
        "manufacturer": None,
        "category_hint": "UNKNOWN",
        "is_cctv_vendor": False,
    }

