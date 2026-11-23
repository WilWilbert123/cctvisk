"""Password recovery workflow and Credential Vault Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RecoveryRecordCreateRequest(BaseModel):
    device_id: int
    manufacturer: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    method_used: str = Field(..., min_length=2, max_length=128)
    status: str = Field(default="IN_PROGRESS", max_length=32)
    notes: str | None = Field(default=None, max_length=2000)


class RecoveryRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    ip_address: str
    manufacturer: str | None = None
    model: str | None = None
    method_used: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class VaultSaveRequest(BaseModel):
    device_id: int
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)
    service_port: int = Field(default=554, ge=1, le=65535)
    notes: str | None = Field(default=None, max_length=500)
    explicit_user_consent: bool = Field(
        ...,
        description="Must be True to confirm explicit user action before encrypting and saving credentials.",
    )


class VaultStatusResponse(BaseModel):
    device_id: int
    has_credentials: bool
    username: str | None = None
    service_port: int | None = None
    notes: str | None = None
    updated_at: str | None = None
    encryption_algorithm: str = "Fernet (AES-128-CBC + HMAC-SHA256)"
    key_storage_notice: str = (
        "Encryption keys are stored outside the SQLite database. If the external key file is lost "
        "or deleted, encrypted credentials cannot be recovered."
    )


class DeviceRecoveryGuideResponse(BaseModel):
    device_id: int
    ip_address: str
    detected_manufacturer: str | None = None
    detected_model: str | None = None
    manufacturer_verified: bool
    requires_manual_identification: bool
    guide: dict[str, Any]
    vault_status: VaultStatusResponse
    history: list[RecoveryRecordResponse] = []

