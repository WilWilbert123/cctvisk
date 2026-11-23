"""Tests for common port metadata, service mapping, and isolated port scanner."""

from __future__ import annotations

import asyncio
import pytest
from backend.services.ports.common_ports import get_common_ports_metadata, get_default_scan_ports
from backend.services.ports.port_scanner import scan_device_ports
from backend.services.ports.service_mapper import (
    infer_protocols_from_ports,
    map_open_ports_to_services,
)


def test_common_ports_and_protocol_mapping() -> None:
    meta = get_common_ports_metadata()
    assert len(meta) >= 10
    default_ports = get_default_scan_ports()
    assert 80 in default_ports
    assert 554 in default_ports

    mapped = map_open_ports_to_services([80, 554, 8000])
    assert len(mapped) == 3
    protocols = infer_protocols_from_ports([80, 554, 8000], onvif_available=True)
    assert "HTTP" in protocols
    assert "RTSP" in protocols
    assert "ONVIF" in protocols
    assert "HIKVISION-SDK" in protocols


@pytest.mark.asyncio
async def test_port_scanner_against_simulated_ports(monkeypatch: pytest.MonkeyPatch) -> None:
    class _DummyWriter:
        def close(self) -> None:
            pass

        async def wait_closed(self) -> None:
            pass

    async def _fake_open_conn(ip: str, port: int):
        if port in (80, 554):
            return object(), _DummyWriter()
        raise ConnectionRefusedError()

    monkeypatch.setattr(asyncio, "open_connection", _fake_open_conn)
    res = await scan_device_ports("192.168.1.50", ports=[80, 443, 554, 8080], timeout_ms=200)
    assert res["open_ports"] == [80, 554]
    assert "RTSP" in res["detected_protocols"]

