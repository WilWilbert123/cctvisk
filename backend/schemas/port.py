"""Port scanning Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from backend.utils.ip_utils import validate_authorized_ip
from backend.utils.validators import validate_port_list


class PortInfoSchema(BaseModel):
    port: int
    protocol: str
    service: str
    description: str
    category_relevance: list[str] = []


class PortScanRequest(BaseModel):
    ip_address: str = Field(..., min_length=7, max_length=45)
    ports: list[int] | None = None
    timeout_ms: int = Field(default=500, ge=100, le=3000)

    @field_validator("ip_address")
    @classmethod
    def check_ip(cls, v: str) -> str:
        return validate_authorized_ip(v)

    @field_validator("ports")
    @classmethod
    def check_ports(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        return validate_port_list(v)

