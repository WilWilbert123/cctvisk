"""Tests for evidence-based CCTV camera classification and anti-false-positive safeguards."""

from __future__ import annotations

from backend.services.cameras.camera_protocols import (
    build_authenticated_rtsp_url,
    get_manufacturer_rtsp_paths,
)
from backend.services.identification.device_classifier import classify_device_from_evidence
from backend.utils.ip_utils import mask_rtsp_url


def test_port_80_or_554_alone_is_not_classified_as_camera() -> None:
    """Requirement: Do not label every device with port 80 or port 554 as a CCTV camera."""
    generic_web_host = {
        "ip_address": "192.168.1.25",
        "mac_address": "FE:AA:BB:CC:DD:EE",
        "hostname": "office-server",
        "mac_vendor": {"manufacturer": None, "category_hint": "UNKNOWN", "is_cctv_vendor": False},
        "manufacturer": None,
        "is_cctv_vendor": False,
        "manufacturer_evidence": [],
        "open_ports": [80],
        "banners": {"http_80": {"reachable": True, "server": "nginx", "title": "Welcome"}},
        "rtsp_verified": False,
        "onvif_info": {},
    }
    res = classify_device_from_evidence(generic_web_host)
    assert res["category"] == "UNKNOWN"

    # Even port 554 open alone without RTSP handshake, vendor OUI, or SDK/banner evidence is UNKNOWN
    ambiguous_554 = dict(generic_web_host)
    ambiguous_554["open_ports"] = [80, 554]
    res2 = classify_device_from_evidence(ambiguous_554)
    assert res2["category"] == "UNKNOWN"


def test_verified_cctv_camera_classification() -> None:
    camera_fp = {
        "ip_address": "192.168.1.108",
        "mac_address": "38:AF:29:11:22:33",
        "hostname": "IPC-HDW",
        "mac_vendor": {
            "manufacturer": "Dahua Technology",
            "category_hint": "CAMERA",
            "is_cctv_vendor": True,
        },
        "manufacturer": "Dahua Technology",
        "is_cctv_vendor": True,
        "manufacturer_evidence": ["MAC OUI 38:AF:29 matched vendor 'Dahua Technology'"],
        "open_ports": [80, 554, 37777],
        "banners": {},
        "rtsp_verified": True,
        "onvif_info": {},
    }
    res = classify_device_from_evidence(camera_fp)
    assert res["category"] == "CAMERA"
    assert res["confidence"] == "HIGH"
    assert res["rtsp_available"] is True


def test_rtsp_url_construction_and_masking() -> None:
    paths = get_manufacturer_rtsp_paths("Hikvision", channel=1, subtype=0)
    assert "/Streaming/Channels/101" in paths

    raw_url = build_authenticated_rtsp_url(
        "192.168.1.64", 554, "/Streaming/Channels/101", "admin", "MySecretPass123"
    )
    masked = mask_rtsp_url(raw_url)
    assert masked == "rtsp://admin:***@192.168.1.64:554/Streaming/Channels/101"
    assert "MySecretPass123" not in (masked or "")

