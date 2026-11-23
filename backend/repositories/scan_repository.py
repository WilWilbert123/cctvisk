"""Repository for NetworkScan, ScanHistory, and ActivityLog records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.constants import ScanStatus
from backend.models.network_scan import NetworkScan
from backend.models.scan_history import ActivityLog, ScanHistory


class ScanRepository:
    """Data access layer for network scan sessions, snapshots, and activity logs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_scan(
        self,
        subnet_cidr: str,
        interface_name: str | None = None,
        local_ip: str | None = None,
        methods_used: list[str] | None = None,
    ) -> NetworkScan:
        scan = NetworkScan(
            subnet_cidr=subnet_cidr,
            interface_name=interface_name,
            local_ip=local_ip,
            status=ScanStatus.RUNNING.value,
            progress=0.0,
            current_stage="Initializing scan",
            methods_used=methods_used or [],
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(scan)
        self.session.commit()
        self.session.refresh(scan)
        return scan

    def get_by_id(self, scan_id: int) -> NetworkScan | None:
        return self.session.get(NetworkScan, scan_id)

    def get_latest_scan(self) -> NetworkScan | None:
        stmt = select(NetworkScan).order_by(NetworkScan.id.desc()).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_scans(self, limit: int = 50) -> list[NetworkScan]:
        stmt = select(NetworkScan).order_by(NetworkScan.id.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def update_scan_progress(
        self,
        scan_id: int,
        progress: float,
        stage: str,
        devices_discovered: int | None = None,
        cameras_discovered: int | None = None,
        nvrs_discovered: int | None = None,
        total_hosts_probed: int | None = None,
    ) -> NetworkScan | None:
        scan = self.get_by_id(scan_id)
        if not scan:
            return None
        scan.progress = round(min(100.0, max(0.0, progress)), 1)
        scan.current_stage = stage
        if devices_discovered is not None:
            scan.devices_discovered = devices_discovered
        if cameras_discovered is not None:
            scan.cameras_discovered = cameras_discovered
        if nvrs_discovered is not None:
            scan.nvrs_discovered = nvrs_discovered
        if total_hosts_probed is not None:
            scan.total_hosts_probed = total_hosts_probed
        self.session.commit()
        self.session.refresh(scan)
        return scan

    def finalize_scan(
        self,
        scan_id: int,
        status: ScanStatus,
        summary: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> NetworkScan | None:
        scan = self.get_by_id(scan_id)
        if not scan:
            return None
        now = datetime.now(timezone.utc)
        scan.status = status.value
        if status == ScanStatus.COMPLETED:
            scan.progress = 100.0
            scan.current_stage = "Scan completed"
        elif status == ScanStatus.CANCELLED:
            scan.current_stage = "Scan cancelled by user"
        elif status == ScanStatus.FAILED:
            scan.current_stage = "Scan failed"
        scan.completed_at = now
        started = scan.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        scan.duration_seconds = round((now - started).total_seconds(), 2)
        if summary is not None:
            scan.scan_summary = summary
        if error_message is not None:
            scan.error_message = error_message
        self.session.commit()
        self.session.refresh(scan)
        return scan

    def add_scan_history_entry(
        self,
        scan_id: int | None,
        device_id: int | None,
        ip_address: str,
        mac_address: str | None,
        manufacturer: str | None,
        category: str,
        confidence: str,
        open_ports: list[int],
        discovery_evidence: dict[str, Any],
    ) -> ScanHistory:
        entry = ScanHistory(
            scan_id=scan_id,
            device_id=device_id,
            ip_address=ip_address,
            mac_address=mac_address,
            manufacturer=manufacturer,
            category=category,
            confidence=confidence,
            open_ports=open_ports,
            discovery_evidence=discovery_evidence,
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def list_scan_history(self, limit: int = 100) -> list[ScanHistory]:
        stmt = select(ScanHistory).order_by(ScanHistory.id.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def log_activity(
        self,
        event_type: str,
        title: str,
        message: str,
        level: str = "info",
        metadata_json: dict[str, Any] | None = None,
    ) -> ActivityLog:
        entry = ActivityLog(
            event_type=event_type,
            level=level,
            title=title,
            message=message,
            metadata_json=metadata_json or {},
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def list_activities(self, limit: int = 100) -> list[ActivityLog]:
        stmt = select(ActivityLog).order_by(ActivityLog.id.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

