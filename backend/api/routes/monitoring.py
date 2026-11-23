"""Background device availability monitoring API routes."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_authorized_client
from backend.repositories.settings_repository import SettingsRepository
from backend.schemas.monitoring import MonitoringConfigUpdateRequest
from backend.services.monitoring.monitor_scheduler import monitor_scheduler

router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
    dependencies=[Depends(require_authorized_client)],
)


@router.get("/status")
def get_monitoring_status() -> dict[str, Any]:
    """Return current monitoring worker status, monitored devices, availability chart series, and alerts."""
    return monitor_scheduler.get_status_snapshot()


@router.post("/start")
def start_monitoring() -> dict[str, Any]:
    """Start the background device availability monitoring loop."""
    monitor_scheduler.start()
    return monitor_scheduler.get_status_snapshot()


@router.post("/stop")
async def stop_monitoring() -> dict[str, Any]:
    """Stop the background device availability monitoring loop."""
    await monitor_scheduler.stop()
    return monitor_scheduler.get_status_snapshot()


@router.patch("/config")
def update_monitoring_config(
    payload: MonitoringConfigUpdateRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Update monitoring interval, timeout, and offline alert settings."""
    monitor_scheduler.configure(
        interval_seconds=payload.interval_seconds,
        timeout_ms=payload.timeout_ms,
        alert_on_offline=payload.alert_on_offline,
    )
    SettingsRepository(db).update_category(
        "monitoring",
        {
            "interval_seconds": payload.interval_seconds,
            "timeout_ms": payload.timeout_ms,
            "alert_on_offline": payload.alert_on_offline,
        },
    )
    return monitor_scheduler.get_status_snapshot()


@router.post("/check-now")
async def trigger_immediate_monitoring_cycle() -> dict[str, Any]:
    """Execute an immediate availability probe across all monitored devices."""
    results = await monitor_scheduler.run_single_cycle()
    snapshot = monitor_scheduler.get_status_snapshot()
    snapshot["last_cycle_results"] = results
    return snapshot

