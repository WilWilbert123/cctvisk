"""Discovery engine Pydantic schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class DiscoveryProbeRequest(BaseModel):
    methods: list[str] = Field(default_factory=lambda: ["onvif", "mdns", "ssdp"])
    timeout_seconds: float = Field(default=2.5, ge=0.5, le=10.0)


class DiscoveryResultsResponse(BaseModel):
    onvif: list[dict[str, Any]] = []
    mdns: list[dict[str, Any]] = []
    ssdp: list[dict[str, Any]] = []
    fingerprints: list[dict[str, Any]] = []
    last_updated: str | None = None

