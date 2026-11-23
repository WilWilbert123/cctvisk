"""Network information, interface listing, subnet validation, and scan control routes."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.dependencies import (
    get_db,
    require_authorized_client,
    require_scan_rate_limit,
)
from backend.core.exceptions import SecurityViolationError
from backend.repositories.scan_repository import ScanRepository
from backend.schemas.network import StartScanRequest, SubnetValidationRequest
from backend.services.network.interface import list_network_interfaces
from backend.services.network.network_info import get_full_network_info
from backend.services.network.subnet import validate_and_describe_subnet
from backend.workers.scan_worker import scan_worker_manager

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("/info", dependencies=[Depends(require_authorized_client)])
def get_network_info(interface_name: str | None = None) -> dict[str, Any]:
    """Return active network adapter, local IPv4, subnet CIDR, gateway, and OS permissions."""
    return get_full_network_info(preferred_interface=interface_name)


@router.get("/interfaces", dependencies=[Depends(require_authorized_client)])
def get_network_interfaces() -> dict[str, Any]:
    """List all active local network interfaces on the host."""
    items = list_network_interfaces()
    return {"items": items, "total": len(items)}


@router.post("/validate-subnet", dependencies=[Depends(require_authorized_client)])
def validate_subnet_endpoint(payload: SubnetValidationRequest) -> dict[str, Any]:
    """Validate whether a manual subnet CIDR belongs to an authorized private network."""
    return validate_and_describe_subnet(payload.subnet_cidr)


@router.post("/scan/start", dependencies=[Depends(require_scan_rate_limit)])
async def start_network_scan(payload: StartScanRequest) -> dict[str, Any]:
    """Start an asynchronous discovery scan on the active or validated local subnet."""
    if not payload.authorized_confirmation:
        raise SecurityViolationError(
            "You must confirm authorization to scan this local network before starting a scan."
        )
    scan_data = scan_worker_manager.start_scan(
        subnet_cidr=payload.subnet_cidr,
        interface_name=payload.interface_name,
        scan_ports=payload.scan_ports,
        enable_onvif=payload.enable_onvif,
        enable_mdns=payload.enable_mdns,
        enable_ssdp=payload.enable_ssdp,
    )
    return scan_data


@router.post("/scan/cancel", dependencies=[Depends(require_authorized_client)])
def cancel_network_scan() -> dict[str, Any]:
    """Cancel an in-progress network scan."""
    return scan_worker_manager.cancel_scan()


@router.get("/scan/status", dependencies=[Depends(require_authorized_client)])
def get_scan_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return current scan progress and latest scan summary."""
    scan_repo = ScanRepository(db)
    latest = scan_repo.get_latest_scan()
    latest_dict = None
    if latest:
        latest_dict = {
            "id": latest.id,
            "subnet_cidr": latest.subnet_cidr,
            "interface_name": latest.interface_name,
            "local_ip": latest.local_ip,
            "status": latest.status,
            "progress": latest.progress,
            "current_stage": latest.current_stage,
            "total_hosts_probed": latest.total_hosts_probed,
            "devices_discovered": latest.devices_discovered,
            "cameras_discovered": latest.cameras_discovered,
            "nvrs_discovered": latest.nvrs_discovered,
            "methods_used": latest.methods_used,
            "scan_summary": latest.scan_summary,
            "error_message": latest.error_message,
            "started_at": latest.started_at.isoformat() if latest.started_at else None,
            "completed_at": latest.completed_at.isoformat() if latest.completed_at else None,
            "duration_seconds": latest.duration_seconds,
        }
    return {
        "is_running": scan_worker_manager.is_running,
        "progress": scan_worker_manager.progress,
        "stage": scan_worker_manager.stage,
        "message": scan_worker_manager.message,
        "devices_found": scan_worker_manager.devices_found,
        "cameras_found": scan_worker_manager.cameras_found,
        "nvrs_found": scan_worker_manager.nvrs_found,
        "current_scan": latest_dict,
    }

