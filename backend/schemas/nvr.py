"""NVR / DVR Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.utils.ip_utils import validate_authorized_ip


class NVRCreateRequest(BaseModel):
    ip_address: str = Field(..., min_length=7, max_length=45)
    recorder_type: str = Field(default="NVR", pattern="^(NVR|DVR)$")
    label: str | None = Field(default=None, max_length=128)
    manufacturer: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    http_port: int = Field(default=80, ge=1, le=65535)
    rtsp_port: int = Field(default=554, ge=1, le=65535)
    sdk_port: int | None = Field(default=8000, ge=1, le=65535)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, v: str) -> str:
        return validate_authorized_ip(v)


class NVRChannelDetectRequest(BaseModel):
    username: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=256)
    onvif_port: int | None = Field(default=None, ge=1, le=65535)
    rtsp_port: int | None = Field(default=None, ge=1, le=65535)


class NVRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    ip_address: str
    mac_address: str | None = None
    hostname: str | None = None
    label: str | None = None
    recorder_type: str = "NVR"
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    http_port: int = 80
    rtsp_port: int = 554
    sdk_port: int | None = None
    onvif_supported: bool = False
    detected_channels: int | None = None
    channels_info: list[dict[str, Any]] = []
    admin_url: str | None = None
    confidence: str = "MEDIUM"
    classification_evidence: list[str] = []
    open_ports: list[int] = []
    is_online: bool = True
    notes: str | None = None
    last_seen: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

