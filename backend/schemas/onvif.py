"""ONVIF discovery and device interrogation Pydantic schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, field_validator
from backend.utils.ip_utils import validate_authorized_ip


class ONVIFInterrogateRequest(BaseModel):
    ip_address: str = Field(..., min_length=7, max_length=45)
    port: int = Field(default=80, ge=1, le=65535)
    username: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=256)

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, v: str) -> str:
        return validate_authorized_ip(v)


class ONVIFDeviceInfoResponse(BaseModel):
    ip_address: str
    port: int
    reachable: bool
    authenticated: bool
    auth_required: bool = False
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    hardware_id: str | None = None
    xaddrs: list[str] = []
    scopes: list[str] = []
    capabilities: dict[str, Any] = {}
    media_profiles: list[dict[str, Any]] = []
    error: str | None = None

