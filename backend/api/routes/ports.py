"""Port scanning API routes for authorized local devices."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.dependencies import (
    get_db,
    require_authorized_client,
    require_scan_rate_limit,
)
from backend.repositories.device_repository import DeviceRepository
from backend.schemas.port import PortScanRequest
from backend.services.ports.common_ports import get_common_ports_metadata
from backend.services.ports.port_scanner import scan_device_ports

router = APIRouter(prefix="/ports", tags=["Ports"])


@router.get("/common", dependencies=[Depends(require_authorized_client)])
def get_common_ports() -> dict[str, Any]:
    """Return the documented catalog of common CCTV and network service ports."""
    items = get_common_ports_metadata()
    return {"items": items, "total": len(items)}


@router.post("/scan", dependencies=[Depends(require_scan_rate_limit)])
async def scan_ports_for_host(
    payload: PortScanRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Perform a controlled TCP port scan on an authorized local IPv4 address."""
    result = await scan_device_ports(
        ip_address=payload.ip_address,
        ports=payload.ports,
        timeout_ms=payload.timeout_ms,
    )
    dev_repo = DeviceRepository(db)
    existing = dev_repo.get_by_ip(payload.ip_address)
    if existing:
        dev_repo.upsert_discovered_device(
            {
                "ip_address": payload.ip_address,
                "open_ports": result["open_ports"],
                "detected_protocols": result["detected_protocols"],
                "is_online": True,
            }
        )
    return result

