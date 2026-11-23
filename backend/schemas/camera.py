"""Camera and Live Stream connection Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.utils.ip_utils import validate_authorized_ip


class CameraCreateRequest(BaseModel):
    ip_address: str = Field(..., min_length=7, max_length=45)
    label: str | None = Field(default=None, max_length=128)
    manufacturer: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    rtsp_port: int = Field(default=554, ge=1, le=65535)
    http_port: int = Field(default=80, ge=1, le=65535)
    onvif_port: int = Field(default=80, ge=1, le=65535)
    rtsp_path: str | None = Field(default="/Streaming/Channels/101", max_length=255)
    username: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=256)
    save_credentials: bool = False
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, v: str) -> str:
        return validate_authorized_ip(v)


class CameraUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=128)
    manufacturer: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    rtsp_port: int | None = Field(default=None, ge=1, le=65535)
    http_port: int | None = Field(default=None, ge=1, le=65535)
    onvif_port: int | None = Field(default=None, ge=1, le=65535)
    rtsp_path: str | None = Field(default=None, max_length=255)
    snapshot_path: str | None = Field(default=None, max_length=255)
    is_favorite: bool | None = None
    notes: str | None = Field(default=None, max_length=1000)


class CameraConnectRequest(BaseModel):
    """Parameters for connecting to a discovered camera and starting a Live View session."""

    username: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=256)
    rtsp_port: int | None = Field(default=None, ge=1, le=65535)
    http_port: int | None = Field(default=None, ge=1, le=65535)
    onvif_port: int | None = Field(default=None, ge=1, le=65535)
    stream_path: str | None = Field(default=None, max_length=255)
    channel: int = Field(default=1, ge=1, le=64)
    subtype: int = Field(default=0, ge=0, le=2)
    protocol: str = Field(default="auto")
    save_credentials: bool = False


class CameraConnectResponse(BaseModel):
    connected: bool
    camera_id: int
    ip_address: str
    stream_type: str
    stream_url: str
    snapshot_url: str
    resolved_rtsp_uri_masked: str | None = None
    media_profiles: list[dict[str, Any]] = []
    requires_auth: bool = False
    message: str


class CameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    ip_address: str
    mac_address: str | None = None
    hostname: str | None = None
    label: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    hardware_id: str | None = None
    confidence: str = "MEDIUM"
    classification_evidence: list[str] = []
    open_ports: list[int] = []
    detected_protocols: list[str] = []
    onvif_supported: bool = False
    onvif_port: int = 80
    onvif_xaddrs: list[str] = []
    onvif_scopes: list[str] = []
    onvif_capabilities: dict[str, Any] = {}
    media_profiles: list[dict[str, Any]] = []
    rtsp_available: bool = False
    rtsp_port: int = 554
    rtsp_path: str | None = None
    rtsp_url_masked: str | None = None
    http_port: int = 80
    https_port: int | None = None
    snapshot_path: str | None = None
    admin_url: str | None = None
    requires_auth: bool = True
    is_online: bool = True
    is_favorite: bool = False
    notes: str | None = None
    has_saved_credentials: bool = False
    saved_username: str | None = None
    stream_active: bool = False
    last_seen: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

