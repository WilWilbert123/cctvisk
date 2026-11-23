"""Tests for NVR and DVR classification and verified channel detection."""

from __future__ import annotations

from backend.services.discovery.nvr_discovery import extract_nvr_candidate_attributes
from backend.services.identification.device_classifier import classify_device_from_evidence


def test_nvr_classification_from_metadata() -> None:
    nvr_fp = {
        "ip_address": "192.168.1.200",
        "mac_address": "28:57:BE:AA:11:22",
        "hostname": "Hikvision-DS-7608NI-I2",
        "mac_vendor": {
            "manufacturer": "Hikvision Digital Technology",
            "category_hint": "CAMERA",
            "is_cctv_vendor": True,
        },
        "manufacturer": "Hikvision Digital Technology",
        "is_cctv_vendor": True,
        "manufacturer_evidence": ["MAC OUI matched Hikvision"],
        "open_ports": [80, 554, 8000],
        "banners": {"http_80": {"title": "DS-7608NI NVR Web"}},
        "rtsp_verified": True,
        "onvif_info": {"reachable": True, "model": "DS-7608NI-I2/8P", "media_profiles": []},
    }
    res = classify_device_from_evidence(nvr_fp)
    assert res["category"] == "NVR"
    assert res["confidence"] == "HIGH"

    attrs = extract_nvr_candidate_attributes("192.168.1.200", res, nvr_fp)
    assert attrs is not None
    assert attrs["recorder_type"] == "NVR"
    # Must NOT invent channel counts when media_profiles is empty
    assert attrs["detected_channels"] is None


def test_dvr_classification_from_port_34567() -> None:
    dvr_fp = {
        "ip_address": "192.168.1.201",
        "mac_address": None,
        "hostname": "xvr-recorder",
        "mac_vendor": {},
        "manufacturer": None,
        "is_cctv_vendor": False,
        "manufacturer_evidence": [],
        "open_ports": [80, 554, 34567],
        "banners": {},
        "rtsp_verified": True,
        "onvif_info": {},
    }
    res = classify_device_from_evidence(dvr_fp)
    assert res["category"] == "DVR"
    assert res["confidence"] == "MEDIUM"

