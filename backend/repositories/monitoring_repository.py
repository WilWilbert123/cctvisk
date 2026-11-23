"""Repository for MonitoringRecord persistence and availability queries."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models.monitoring import MonitoringRecord


class MonitoringRepository:
    """Data access layer for device availability monitoring records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_record(
        self,
        device_id: int,
        ip_address: str,
        is_online: bool,
        status_changed: bool = False,
        latency_ms: float | None = None,
        probe_method: str = "TCP/ICMP",
        event_message: str | None = None,
    ) -> MonitoringRecord:
        record = MonitoringRecord(
            device_id=device_id,
            ip_address=ip_address,
            is_online=is_online,
            status_changed=status_changed,
            latency_ms=latency_ms,
            probe_method=probe_method,
            event_message=event_message,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_recent_records(self, limit: int = 100) -> list[MonitoringRecord]:
        stmt = select(MonitoringRecord).order_by(MonitoringRecord.id.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def list_status_change_alerts(self, limit: int = 50) -> list[MonitoringRecord]:
        stmt = (
            select(MonitoringRecord)
            .where(MonitoringRecord.status_changed.is_(True))
            .order_by(MonitoringRecord.id.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_for_device(self, device_id: int, limit: int = 50) -> list[MonitoringRecord]:
        stmt = (
            select(MonitoringRecord)
            .where(MonitoringRecord.device_id == device_id)
            .order_by(MonitoringRecord.id.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

