"""Manufacturer identification combining ONVIF metadata, MAC OUI, HTTP/RTSP banners, and mDNS/SSDP."""

from __future__ import annotations

from typing import Any
from backend.services.identification.mac_lookup import lookup_mac_vendor

KNOWN_VENDOR_SIGNATURES: list[tuple[str, str, bool]] = [
    ("hikvision", "Hikvision Digital Technology", True),
    ("dnvrs-webs", "Hikvision Digital Technology", True),
    ("hik-connect", "Hikvision Digital Technology", True),
    ("app-webs", "Hikvision Digital Technology", True),
    ("dahua", "Dahua Technology", True),
    ("dh_ipc", "Dahua Technology", True),
    ("reolink", "Reolink Innovation", True),
    ("axis", "Axis Communications", True),
    ("amcrest", "Amcrest Technologies", True),
    ("uniview", "Uniview Technologies", True),
    ("hanwha", "Hanwha Vision", True),
    ("techwin", "Hanwha Vision", True),
    ("vivotek", "Vivotek", True),
    ("bosch", "Bosch Security Systems", True),
    ("tp-link", "TP-Link Corporation", False),
    ("tapo", "TP-Link (Tapo)", True),
    ("ubiquiti", "Ubiquiti Inc.", False),
    ("unifi", "Ubiquiti Inc.", False),
    ("synology", "Synology Inc.", False),
    ("hewlett packard", "Hewlett Packard", False),
    ("hp ", "Hewlett Packard", False),
    ("brother", "Brother Industries", False),
    ("epson", "Seiko Epson", False),
    ("rap2200", "Ruijie Networks", False),
    ("rg-es", "Ruijie Networks", False),
    ("ruijie", "Ruijie Networks", False),
    ("reyee", "Ruijie Networks", False),
    ("xiaomi", "Xiaomi Communications", False),
    ("redmi", "Xiaomi (Redmi)", False),
    ("poco", "Xiaomi (POCO)", False),
    ("realme", "Realme Mobile", False),
    ("oppo", "OPPO Mobile", False),
    ("vivo", "Vivo Mobile", False),
    ("s23-ultra", "Samsung Electronics", False),
    ("s24-ultra", "Samsung Electronics", False),
    ("galaxy", "Samsung Electronics", False),
    ("samsung", "Samsung Electronics", False),
    ("iphone", "Apple, Inc.", False),
    ("ipad", "Apple, Inc.", False),
    ("macbook", "Apple, Inc.", False),
    ("lmu-lx9", "Honor Device Co.", False),
    ("honor", "Honor Device Co.", False),
    ("huawei", "Huawei Technologies", False),
]


def identify_manufacturer(
    mac_address: str | None = None,
    onvif_manufacturer: str | None = None,
    banners: dict[str, Any] | None = None,
    hostname: str | None = None,
    mdns_info: dict[str, Any] | None = None,
    ssdp_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Identify device manufacturer strictly from verifiable discovery signals.
    Returns manufacturer name (or None if unknown), source evidence, and whether it is a known CCTV vendor.
    """
    evidence: list[str] = []

    # 1. Explicit ONVIF manufacturer is highest-fidelity
    if onvif_manufacturer and onvif_manufacturer.strip():
        clean_onvif = onvif_manufacturer.strip()
        evidence.append(f"ONVIF GetDeviceInformation reported manufacturer '{clean_onvif}'")
        is_cctv = True
        return {
            "manufacturer": clean_onvif,
            "is_cctv_vendor": is_cctv,
            "evidence": evidence,
        }

    # 2. Local MAC OUI lookup
    mac_info = lookup_mac_vendor(mac_address)
    if mac_info.get("manufacturer"):
        mfg = mac_info["manufacturer"]
        evidence.append(f"MAC OUI {mac_info['oui']} matched vendor '{mfg}'")
        return {
            "manufacturer": mfg,
            "is_cctv_vendor": bool(mac_info.get("is_cctv_vendor", False)),
            "evidence": evidence,
        }

    # 3. Inspect service banners, SSDP server headers, mDNS properties, and hostname
    combined_text_parts: list[str] = []
    if banners:
        for k, v in banners.items():
            combined_text_parts.append(f"{k}:{v}")
    if hostname:
        combined_text_parts.append(hostname)
    if mdns_info:
        combined_text_parts.append(str(mdns_info))
    if ssdp_info:
        combined_text_parts.append(str(ssdp_info))

    haystack = " ".join(combined_text_parts).lower()
    for token, canonical_mfg, is_cctv in KNOWN_VENDOR_SIGNATURES:
        if token in haystack:
            evidence.append(f"Service metadata/banner signature matched '{canonical_mfg}' ({token})")
            return {
                "manufacturer": canonical_mfg,
                "is_cctv_vendor": is_cctv,
                "evidence": evidence,
            }

    return {
        "manufacturer": None,
        "is_cctv_vendor": False,
        "evidence": [],
    }

