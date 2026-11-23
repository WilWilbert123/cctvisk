"""Dashboard API routes returning real-time network and SQLite persistence statistics."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_authorized_client
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.monitoring_repository import MonitoringRepository
from backend.repositories.recovery_repository import RecoveryRepository
from backend.repositories.scan_repository import ScanRepository
from backend.services.network.interface import get_active_interface

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(require_authorized_client)])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return real dashboard statistics, active network interface, recent devices, and monitoring events."""
    dev_repo = DeviceRepository(db)
    scan_repo = ScanRepository(db)
    mon_repo = MonitoringRepository(db)
    rec_repo = RecoveryRepository(db)

    active_iface = get_active_interface()
    counts = dev_repo.get_counts()
    latest_scan = scan_repo.get_latest_scan()
    all_devices = dev_repo.get_all()
    vault_ids = rec_repo.list_vault_device_ids()

    recent_devices_sorted = sorted(
        all_devices,
        key=lambda d: (d.last_seen or d.updated_at or d.created_at),
        reverse=True,
    )[:10]

    recent_devices_payload = [
        {
            "id": d.id,
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "manufacturer": d.manufacturer,
            "model": d.model,
            "hostname": d.hostname,
            "label": d.label,
            "category": d.category,
            "confidence": d.confidence,
            "classification_evidence": d.classification_evidence,
            "open_ports": d.open_ports,
            "detected_protocols": d.detected_protocols,
            "onvif_available": d.onvif_available,
            "rtsp_available": d.rtsp_available,
            "is_online": d.is_online,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "camera_id": d.camera.id if d.camera else None,
            "nvr_id": d.nvr.id if d.nvr else None,
            "has_saved_credentials": d.id in vault_ids,
        }
        for d in recent_devices_sorted
    ]

    mon_records = mon_repo.list_recent_records(limit=15)
    monitoring_activity = [
        {
            "id": r.id,
            "device_id": r.device_id,
            "ip_address": r.ip_address,
            "is_online": r.is_online,
            "status_changed": r.status_changed,
            "latency_ms": r.latency_ms,
            "probe_method": r.probe_method,
            "event_message": r.event_message,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
        }
        for r in mon_records
    ]

    category_tally: dict[str, int] = {}
    for d in all_devices:
        category_tally[d.category] = category_tally.get(d.category, 0) + 1

    status_distribution = [
        {"name": cat, "value": cnt, "category": cat}
        for cat, cnt in sorted(category_tally.items())
    ]

    activities = scan_repo.list_activities(limit=15)
    recent_events = [
        {
            "id": a.id,
            "type": a.event_type,
            "level": a.level,
            "title": a.title,
            "message": a.message,
            "timestamp": a.created_at.isoformat() if a.created_at else "",
        }
        for a in activities
    ]

    latest_scan_payload = None
    if latest_scan:
        latest_scan_payload = {
            "id": latest_scan.id,
            "subnet_cidr": latest_scan.subnet_cidr,
            "interface_name": latest_scan.interface_name,
            "local_ip": latest_scan.local_ip,
            "status": latest_scan.status,
            "progress": latest_scan.progress,
            "current_stage": latest_scan.current_stage,
            "total_hosts_probed": latest_scan.total_hosts_probed,
            "devices_discovered": latest_scan.devices_discovered,
            "cameras_discovered": latest_scan.cameras_discovered,
            "nvrs_discovered": latest_scan.nvrs_discovered,
            "methods_used": latest_scan.methods_used,
            "started_at": latest_scan.started_at.isoformat() if latest_scan.started_at else None,
            "completed_at": latest_scan.completed_at.isoformat() if latest_scan.completed_at else None,
            "duration_seconds": latest_scan.duration_seconds,
        }

    return {
        "network": {
            "interface_name": active_iface["interface_name"],
            "ip_address": active_iface["ip_address"],
            "subnet_cidr": active_iface["subnet_cidr"],
            "netmask": active_iface["netmask"],
            "gateway": active_iface.get("gateway"),
            "mac_address": active_iface.get("mac_address"),
            "is_connected": active_iface.get("is_up", False),
            "connection_type": active_iface.get("connection_type", "Ethernet/Wi-Fi"),
            "ssid": active_iface.get("ssid"),
        },
        "counts": counts,
        "latest_scan": latest_scan_payload,
        "recent_devices": recent_devices_payload,
        "monitoring_activity": monitoring_activity,
        "status_distribution": status_distribution,
        "recent_events": recent_events,
    }

