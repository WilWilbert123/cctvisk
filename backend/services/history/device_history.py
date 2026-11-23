"""Retrieves device status transitions and historical discovery records."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.monitoring_repository import MonitoringRepository


def get_device_history_summary(session: Session, limit: int = 100) -> dict[str, Any]:
    dev_repo = DeviceRepository(session)
    mon_repo = MonitoringRepository(session)
    devices = dev_repo.get_all()
    status_events = mon_repo.list_recent_records(limit=limit)
    return {
        "devices": devices,
        "status_events": status_events,
    }

