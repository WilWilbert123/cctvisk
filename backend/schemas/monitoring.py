"""Background monitoring Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class MonitoringConfigUpdateRequest(BaseModel):
    interval_seconds: int = Field(..., ge=10, le=3600)
    timeout_ms: int = Field(default=1000, ge=200, le=5000)
    alert_on_offline: bool = True


class MonitoringEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    ip_address: str
    is_online: bool
    status_changed: bool
    latency_ms: float | None = None
    probe_method: str
    event_message: str | None = None
    checked_at: datetime


class MonitoringStatusResponse(BaseModel):
    is_running: bool
    interval_seconds: int
    timeout_ms: int
    alert_on_offline: bool = True
    total_monitored: int
    online_count: int
    offline_count: int
    last_cycle_at: str | None = None
    devices: list[dict[str, Any]] = []
    availability_series: list[dict[str, Any]] = []
    recent_alerts: list[dict[str, Any]] = []

