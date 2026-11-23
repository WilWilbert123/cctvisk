"""History API routes for previous scans, discovered devices, recovery logs, and system activity."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_authorized_client
from backend.services.history.activity_history import get_activity_history_summary
from backend.services.history.device_history import get_device_history_summary
from backend.services.history.scan_history import get_scan_history_summary

router = APIRouter(
    prefix="/history",
    tags=["History"],
    dependencies=[Depends(require_authorized_client)],
)


@router.get("/scans")
def get_scans_history(
    limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return past network scan sessions and device snapshots."""
    summary = get_scan_history_summary(db, limit=limit)
    scans = [
        {
            "id": s.id,
            "subnet_cidr": s.subnet_cidr,
            "interface_name": s.interface_name,
            "local_ip": s.local_ip,
            "status": s.status,
            "progress": s.progress,
            "total_hosts_probed": s.total_hosts_probed,
            "devices_discovered": s.devices_discovered,
            "cameras_discovered": s.cameras_discovered,
            "nvrs_discovered": s.nvrs_discovered,
            "methods_used": s.methods_used,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "duration_seconds": s.duration_seconds,
        }
        for s in summary["scans"]
    ]
    return {"items": scans, "total": len(scans)}


@router.get("/devices")
def get_devices_history(
    limit: int = Query(default=100, ge=1, le=300), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return historical device discovery snapshots and status change events."""
    summary = get_device_history_summary(db, limit=limit)
    events = [
        {
            "id": e.id,
            "device_id": e.device_id,
            "ip_address": e.ip_address,
            "is_online": e.is_online,
            "status_changed": e.status_changed,
            "latency_ms": e.latency_ms,
            "probe_method": e.probe_method,
            "event_message": e.event_message,
            "checked_at": e.checked_at.isoformat() if e.checked_at else None,
        }
        for e in summary["status_events"]
    ]
    return {"items": events, "total": len(events)}


@router.get("/recovery")
def get_recovery_history(
    limit: int = Query(default=100, ge=1, le=300), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return password recovery workflow history."""
    summary = get_activity_history_summary(db, limit=limit)
    items = [
        {
            "id": r.id,
            "device_id": r.device_id,
            "ip_address": r.ip_address,
            "manufacturer": r.manufacturer,
            "model": r.model,
            "method_used": r.method_used,
            "status": r.status,
            "notes": r.notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in summary["recoveries"]
    ]
    return {"items": items, "total": len(items)}


@router.get("/activity")
def get_activity_logs(
    limit: int = Query(default=100, ge=1, le=300), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return unified system audit and activity logs."""
    summary = get_activity_history_summary(db, limit=limit)
    items = [
        {
            "id": a.id,
            "event_type": a.event_type,
            "level": a.level,
            "title": a.title,
            "message": a.message,
            "metadata": a.metadata_json,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in summary["activities"]
    ]
    return {"items": items, "total": len(items)}

