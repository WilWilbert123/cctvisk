"""System health, diagnostics, and remote LAN pairing API routes."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.dependencies import require_authorized_client
from backend.core.exceptions import SecurityViolationError
from backend.core.security import verify_api_token
from backend.services.system.diagnostics import get_full_system_diagnostics
from backend.services.system.health_check import perform_system_health_check

router = APIRouter(prefix="/system", tags=["System"])


class PairingRequest(BaseModel):
    token: str


@router.get("/health")
def system_health() -> dict[str, Any]:
    """Return application health, SQLite status, FFmpeg availability, and worker state."""
    return perform_system_health_check()


@router.get("/diagnostics", dependencies=[Depends(require_authorized_client)])
def system_diagnostics() -> dict[str, Any]:
    """Return complete platform diagnostics, permissions, firewall rules, and Android PWA LAN guide."""
    return get_full_system_diagnostics()


@router.post("/pair")
def pair_remote_lan_client(payload: PairingRequest) -> dict[str, Any]:
    """Verify the local API pairing token for remote LAN / Android PWA dashboard access."""
    if not verify_api_token(payload.token):
        raise SecurityViolationError("Invalid API pairing token.")
    return {
        "paired": True,
        "message": "Successfully paired with CCTV Network Discovery & Recovery Assistant host.",
    }

