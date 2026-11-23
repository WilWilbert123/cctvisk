"""Monitoring event alert creation and WebSocket notification broadcasting."""

from __future__ import annotations

from typing import Any
from backend.core.events import event_manager
from backend.models.device import Device
from backend.models.monitoring import MonitoringRecord


async def dispatch_status_change_alert(
    device: Device,
    record: MonitoringRecord,
    previous_online: bool,
) -> dict[str, Any]:
    """Broadcast real-time WebSocket notifications when a monitored device goes offline or reconnects."""
    name = device.label or device.hostname or device.manufacturer or device.ip_address
    new_state = "ONLINE" if record.is_online else "OFFLINE"
    msg = (
        f"Device {name} ({device.ip_address}) reconnected ({record.latency_ms or 0} ms)."
        if record.is_online
        else f"Device {name} ({device.ip_address}) went OFFLINE."
    )
    alert_payload = {
        "id": record.id,
        "device_id": device.id,
        "ip_address": device.ip_address,
        "hostname": name,
        "category": device.category,
        "previous_online": previous_online,
        "is_online": record.is_online,
        "status": new_state,
        "latency_ms": record.latency_ms,
        "message": msg,
        "timestamp": record.checked_at.isoformat() if record.checked_at else "",
    }
    await event_manager.broadcast(
        "device_status_changed",
        {
            "device_id": device.id,
            "ip_address": device.ip_address,
            "is_online": record.is_online,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        },
    )
    await event_manager.broadcast("monitoring_event", alert_payload)
    if device.category in ("CAMERA", "NVR", "DVR") or device.is_favorite:
        await event_manager.broadcast(
            "system_notification",
            {
                "level": "success" if record.is_online else "warning",
                "title": f"Device {new_state}",
                "message": msg,
            },
        )
    return alert_payload

