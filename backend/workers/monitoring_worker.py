"""Background monitoring worker wrapper around MonitorScheduler."""

from __future__ import annotations

from backend.services.monitoring.monitor_scheduler import monitor_scheduler


def start_monitoring_worker() -> None:
    monitor_scheduler.start()


async def stop_monitoring_worker() -> None:
    await monitor_scheduler.stop()

