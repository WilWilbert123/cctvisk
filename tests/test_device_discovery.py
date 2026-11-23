"""Tests for device fingerprinting, MAC OUI lookup, SSDP parsing, and multi-method discovery."""

from __future__ import annotations

import pytest
from backend.services.discovery.device_discovery import enrich_and_classify_host
from backend.services.discovery.ssdp_discovery import parse_ssdp_response
from backend.services.identification.mac_lookup import lookup_mac_vendor


def test_mac_oui_vendor_lookup() -> None:
    hik = lookup_mac_vendor("28:57:BE:11:22:33")
    assert hik["manufacturer"] == "Hikvision Digital Technology"
    assert hik["is_cctv_vendor"] is True

    unknown = lookup_mac_vendor("FE:DC:BA:98:76:54")
    assert unknown["manufacturer"] is None
    assert unknown["is_cctv_vendor"] is False


def test_ssdp_response_parsing() -> None:
    raw = (
        "HTTP/1.1 200 OK\r\n"
        "SERVER: Linux/3.10 UPnP/1.0 Hikvision-IPCam/1.0\r\n"
        "LOCATION: http://192.168.1.64:80/upnp/device.xml\r\n"
        "ST: upnp:rootdevice\r\n"
        "USN: uuid:1234\r\n\r\n"
    )
    parsed = parse_ssdp_response(raw, "192.168.1.64")
    assert parsed is not None
    assert parsed["ip_address"] == "192.168.1.64"
    assert "Hikvision" in parsed["server"]


@pytest.mark.asyncio
async def test_enrich_and_classify_host_isolated(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_resolve_hostname(_ip: str, timeout_seconds: float = 1.0):
        return "ipcam-frontdoor.local"

    async def _fake_inspect_services(_ip: str, _ports: list[int]):
        return {
            "banners": {"http_80": {"reachable": True, "server": "DNVRS-Webs", "title": "Hikvision"}},
            "rtsp_verified": True,
        }

    async def _fake_interrogate_onvif(_ip: str, port: int = 80, username=None, password=None):
        return {"reachable": False}

    monkeypatch.setattr(
        "backend.services.identification.device_fingerprint.resolve_hostname",
        _fake_resolve_hostname,
    )
    monkeypatch.setattr(
        "backend.services.identification.device_fingerprint.inspect_device_services",
        _fake_inspect_services,
    )
    monkeypatch.setattr(
        "backend.services.discovery.device_discovery.interrogate_onvif_device",
        _fake_interrogate_onvif,
    )

    result = await enrich_and_classify_host(
        ip_address="192.168.1.64",
        host_base={
            "ip_address": "192.168.1.64",
            "mac_address": "28:57:BE:01:02:03",
            "quick_open_ports": [80, 554, 8000],
            "discovery_methods": ["ARP", "TCP"],
        },
        onvif_by_ip={},
        mdns_by_ip={},
        ssdp_by_ip={},
        scan_ports=False,
    )
    assert result["category"] == "CAMERA"
    assert result["confidence"] == "HIGH"
    assert result["manufacturer"] == "Hikvision Digital Technology"
    assert result["camera_attributes"] is not None
