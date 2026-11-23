"""Tests for background device monitoring, status transitions, and availability series."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.monitoring_repository import MonitoringRepository
from backend.services.monitoring.availability import compute_availability_series
from backend.services.monitoring.device_monitor import probe_and_record_device


@pytest.mark.asyncio
async def test_device_monitoring_and_transition_recording(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    dev_repo = DeviceRepository(db_session)
    dev = dev_repo.upsert_discovered_device(
        {
            "ip_address": "192.168.1.90",
            "category": "CAMERA",
            "confidence": "HIGH",
            "is_online": True,
            "is_monitored": True,
        }
    )

    async def _fake_offline(_ip: str, timeout_ms: int = 1000, enable_icmp: bool = True):
        return False, None, [], "NONE"

    monkeypatch.setattr(
        "backend.services.monitoring.device_monitor.check_host_reachable",
        _fake_offline,
    )

    res = await probe_and_record_device(db_session, dev, timeout_ms=300)
    assert res["is_online"] is False
    assert res["status_changed"] is True

    mon_repo = MonitoringRepository(db_session)
    records = mon_repo.list_for_device(dev.id)
    assert len(records) == 1
    assert records[0].status_changed is True

    series = compute_availability_series(records)
    assert len(series) == 1
    assert series[0]["online_numeric"] == 0

