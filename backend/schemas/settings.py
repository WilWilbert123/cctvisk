"""Application settings Pydantic schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class SettingsUpdateRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=64)
    values: dict[str, Any]


class SettingsOverviewResponse(BaseModel):
    settings: dict[str, dict[str, Any]]
    vault_status: dict[str, Any]
    database_health: dict[str, Any]
    lan_access: dict[str, Any]

