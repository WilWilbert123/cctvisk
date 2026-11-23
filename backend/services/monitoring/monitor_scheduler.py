"""Non-overlapping asynchronous monitoring scheduler and cycle runner."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from backend.app.config import get_settings
from backend.core.logging import get_logger
from backend.database.session import session_scope
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.monitoring_repository import MonitoringRepository
from backend.services.monitoring.availability import compute_availability_series
from backend.services.monitoring.device_monitor import probe_and_record_device

logger = get_logger("monitor_scheduler")


class MonitorScheduler:
    """
    Background device availability scheduler.
    Uses an asyncio.Lock to guarantee monitoring jobs never overlap.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.is_running: bool = False
        self.interval_seconds: int = settings.MONITORING_INTERVAL_SECONDS
        self.timeout_ms: int = settings.MONITORING_TIMEOUT_MS
        self.alert_on_offline: bool = True
        self.last_cycle_at: str | None = None
        self._task: asyncio.Task[None] | None = None
        self._cycle_lock = asyncio.Lock()

    async def run_single_cycle(self) -> list[dict[str, Any]]:
        """Execute one non-overlapping monitoring check across all monitored devices."""
        if self._cycle_lock.locked():
            logger.debug("Skipping monitoring cycle because previous cycle is still active.")
            return []

        async with self._cycle_lock:
            results: list[dict[str, Any]] = []
            with session_scope() as session:
                dev_repo = DeviceRepository(session)
                devices = dev_repo.get_monitored_devices()
                for dev in devices:
                    try:
                        res = await probe_and_record_device(
                            session, dev, timeout_ms=self.timeout_ms
                        )
                        results.append(res)
                    except Exception as exc:
                        logger.debug("Error monitoring device %s: %s", dev.ip_address, exc)

            self.last_cycle_at = datetime.now(timezone.utc).isoformat()
            return results

    async def _loop(self) -> None:
        logger.info(
            "Background device monitoring started (interval=%ds)", self.interval_seconds
        )
        while self.is_running:
            try:
                await self.run_single_cycle()
            except Exception as exc:
                logger.error("Monitoring loop error: %s", exc)
            await asyncio.sleep(max(10, self.interval_seconds))

    def start(self) -> None:
        if self.is_running and self._task and not self._task.done():
            return
        self.is_running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._loop())
        except RuntimeError:
            pass

    async def stop(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Background device monitoring stopped.")

    def configure(
        self,
        interval_seconds: int,
        timeout_ms: int = 1000,
        alert_on_offline: bool = True,
    ) -> None:
        self.interval_seconds = max(10, min(3600, int(interval_seconds)))
        self.timeout_ms = max(200, min(5000, int(timeout_ms)))
        self.alert_on_offline = bool(alert_on_offline)

    def get_status_snapshot(self) -> dict[str, Any]:
        with session_scope() as session:
            dev_repo = DeviceRepository(session)
            mon_repo = MonitoringRepository(session)
            monitored = dev_repo.get_monitored_devices()
            recent_records = mon_repo.list_recent_records(limit=60)
            alerts = mon_repo.list_status_change_alerts(limit=25)

            online_count = sum(1 for d in monitored if d.is_online)
            offline_count = len(monitored) - online_count

            devices_payload = [
                {
                    "id": d.id,
                    "ip_address": d.ip_address,
                    "mac_address": d.mac_address,
                    "hostname": d.label or d.hostname or d.ip_address,
                    "manufacturer": d.manufacturer,
                    "category": d.category,
                    "is_online": d.is_online,
                    "latency_ms": d.latency_ms,
                    "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                }
                for d in monitored
            ]
            alerts_payload = [
                {
                    "id": a.id,
                    "device_id": a.device_id,
                    "ip_address": a.ip_address,
                    "is_online": a.is_online,
                    "status": "ONLINE" if a.is_online else "OFFLINE",
                    "latency_ms": a.latency_ms,
                    "message": a.event_message or f"Host {a.ip_address} status changed",
                    "timestamp": a.checked_at.isoformat() if a.checked_at else "",
                }
                for a in alerts
            ]
            series = compute_availability_series(recent_records)

            return {
                "is_running": self.is_running,
                "interval_seconds": self.interval_seconds,
                "timeout_ms": self.timeout_ms,
                "alert_on_offline": self.alert_on_offline,
                "total_monitored": len(monitored),
                "online_count": online_count,
                "offline_count": offline_count,
                "last_cycle_at": self.last_cycle_at,
                "devices": devices_payload,
                "availability_series": series,
                "recent_alerts": alerts_payload,
            }


monitor_scheduler = MonitorScheduler()

