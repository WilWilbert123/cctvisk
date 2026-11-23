"""Checks availability for general monitored LAN devices."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from backend.models.device import Device
from backend.repositories.monitoring_repository import MonitoringRepository
from backend.repositories.scan_repository import ScanRepository
from backend.services.monitoring.alerts import dispatch_status_change_alert
from backend.services.network.ping import check_host_reachable


async def probe_and_record_device(
    session: Session, device: Device, timeout_ms: int = 1000
) -> dict[str, Any]:
    """Perform a liveness check on a single Device and persist a MonitoringRecord."""
    previous_online = bool(device.is_online)
    is_online, latency_ms, _open_ports, method = await check_host_reachable(
        device.ip_address, timeout_ms=timeout_ms, enable_icmp=True
    )

    status_changed = is_online != previous_online
    now = datetime.now(timezone.utc)
    device.is_online = is_online
    if is_online:
        device.last_seen = now
        device.latency_ms = latency_ms
    session.commit()

    mon_repo = MonitoringRepository(session)
    event_msg = None
    if status_changed:
        event_msg = (
            f"Device {device.ip_address} transitioned to {'ONLINE' if is_online else 'OFFLINE'}"
        )

    rec = mon_repo.add_record(
        device_id=device.id,
        ip_address=device.ip_address,
        is_online=is_online,
        status_changed=status_changed,
        latency_ms=latency_ms,
        probe_method=method,
        event_message=event_msg,
    )

    if status_changed:
        scan_repo = ScanRepository(session)
        scan_repo.log_activity(
            event_type="device_status_change",
            title="Device Availability Changed",
            message=event_msg or "",
            level="info" if is_online else "warning",
            metadata_json={"device_id": device.id, "ip_address": device.ip_address, "is_online": is_online},
        )
        await dispatch_status_change_alert(device, rec, previous_online)

    return {
        "device_id": device.id,
        "ip_address": device.ip_address,
        "is_online": is_online,
        "status_changed": status_changed,
        "latency_ms": latency_ms,
    }

