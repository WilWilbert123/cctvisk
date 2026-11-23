"""Device Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.utils.ip_utils import validate_authorized_ip


class DeviceCreateRequest(BaseModel):
    ip_address: str = Field(..., min_length=7, max_length=45)
    mac_address: str | None = None
    label: str | None = Field(default=None, max_length=128)
    category: str = Field(default="UNKNOWN", max_length=32)
    manufacturer: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    hostname: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, v: str) -> str:
        return validate_authorized_ip(v)


class DeviceUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=32)
    manufacturer: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=1000)
    is_favorite: bool | None = None
    is_monitored: bool | None = None


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: str
    mac_address: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    hostname: str | None = None
    label: str | None = None
    category: str
    confidence: str
    classification_evidence: list[str] = []
    open_ports: list[int] = []
    service_banners: dict[str, Any] = {}
    detected_protocols: list[str] = []
    discovery_methods: list[str] = []
    onvif_available: bool = False
    rtsp_available: bool = False
    is_online: bool = True
    is_monitored: bool = True
    is_favorite: bool = False
    is_manual: bool = False
    latency_ms: float | None = None
    notes: str | None = None
    last_seen: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    camera_id: int | None = None
    nvr_id: int | None = None
    has_saved_credentials: bool = False

