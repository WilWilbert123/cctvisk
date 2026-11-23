"""Network interface and scanning Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.utils.ip_utils import validate_authorized_subnet


class NetworkInterfaceSchema(BaseModel):
    interface_name: str
    ip_address: str
    netmask: str
    subnet_cidr: str
    gateway: str | None = None
    mac_address: str | None = None
    is_up: bool = True
    connection_type: str = "Ethernet/Wi-Fi"
    ssid: str | None = None
    speed_mbps: int | None = None


class SubnetValidationRequest(BaseModel):
    subnet_cidr: str = Field(..., min_length=7, max_length=45)


class SubnetValidationResponse(BaseModel):
    valid: bool
    normalized_cidr: str | None = None
    host_count: int = 0
    message: str


class StartScanRequest(BaseModel):
    subnet_cidr: str | None = None
    interface_name: str | None = None
    authorized_confirmation: bool = Field(
        default=True,
        description="Confirmation that the user owns or is authorized to scan this local subnet.",
    )
    scan_ports: bool = True
    enable_onvif: bool = True
    enable_mdns: bool = True
    enable_ssdp: bool = True

    @field_validator("subnet_cidr")
    @classmethod
    def check_subnet(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        net = validate_authorized_subnet(v.strip())
        return str(net)


class NetworkScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subnet_cidr: str
    interface_name: str | None = None
    local_ip: str | None = None
    status: str
    progress: float
    current_stage: str | None = None
    total_hosts_probed: int
    devices_discovered: int
    cameras_discovered: int
    nvrs_discovered: int
    methods_used: list[str]
    scan_summary: dict[str, Any]
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None

