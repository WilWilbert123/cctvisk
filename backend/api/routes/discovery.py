"""Discovery protocol evidence API routes (ONVIF, mDNS, SSDP, fingerprints)."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from backend.app.dependencies import require_authorized_client, require_scan_rate_limit
from backend.schemas.discovery import DiscoveryProbeRequest
from backend.services.discovery.device_discovery import (
    discovery_state,
    run_targeted_discovery_probes,
)

router = APIRouter(prefix="/discovery", tags=["Discovery"])


@router.get("/results", dependencies=[Depends(require_authorized_client)])
def get_discovery_results() -> dict[str, Any]:
    """Return the latest collected ONVIF, mDNS, SSDP, and fingerprint evidence."""
    return discovery_state.snapshot()


@router.post("/probe", dependencies=[Depends(require_scan_rate_limit)])
async def trigger_discovery_probe(payload: DiscoveryProbeRequest) -> dict[str, Any]:
    """Execute an active multicast discovery probe for ONVIF, mDNS, and SSDP."""
    return await run_targeted_discovery_probes(
        methods=payload.methods,
        timeout_seconds=payload.timeout_seconds,
    )

