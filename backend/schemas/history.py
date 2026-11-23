"""History and audit log Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class ScanHistoryItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int | None = None
    device_id: int | None = None
    ip_address: str
    mac_address: str | None = None
    manufacturer: str | None = None
    category: str
    confidence: str
    open_ports: list[int] = []
    discovery_evidence: dict[str, Any] = {}
    recorded_at: datetime


class ActivityLogItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    level: str
    title: str
    message: str
    metadata_json: dict[str, Any] = {}
    created_at: datetime

