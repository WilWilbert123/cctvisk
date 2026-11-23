"""Calculates device uptime percentages and chart time-series from real MonitoringRecord rows."""

from __future__ import annotations

from typing import Any
from backend.models.monitoring import MonitoringRecord


def compute_availability_series(records: list[MonitoringRecord]) -> list[dict[str, Any]]:
    """Build chronological chart points from actual monitoring records."""
    ordered = list(reversed(records[:40]))
    series: list[dict[str, Any]] = []
    for rec in ordered:
        ts = rec.checked_at.strftime("%H:%M:%S") if rec.checked_at else ""
        series.append(
            {
                "id": rec.id,
                "timestamp": rec.checked_at.isoformat() if rec.checked_at else "",
                "time_label": ts,
                "ip_address": rec.ip_address,
                "is_online": rec.is_online,
                "online_numeric": 100 if rec.is_online else 0,
                "latency_ms": rec.latency_ms or 0.0,
            }
        )
    return series

