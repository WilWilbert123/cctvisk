"""ONVIF multicast discovery and SOAP device interrogation API routes."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.dependencies import (
    get_db,
    require_authorized_client,
    require_scan_rate_limit,
)
from backend.repositories.camera_repository import CameraRepository
from backend.repositories.device_repository import DeviceRepository
from backend.schemas.onvif import ONVIFInterrogateRequest
from backend.services.discovery.onvif_discovery import (
    interrogate_onvif_device,
    run_onvif_discovery_with_enrichment,
)

router = APIRouter(prefix="/onvif", tags=["ONVIF"])


@router.post("/discover", dependencies=[Depends(require_scan_rate_limit)])
async def discover_onvif_endpoint(timeout_seconds: float = 2.5) -> dict[str, Any]:
    """Execute UDP multicast WS-Discovery for ONVIF devices on the local network."""
    items = await run_onvif_discovery_with_enrichment(timeout_seconds=timeout_seconds)
    return {"items": items, "total": len(items)}


@router.post("/interrogate", dependencies=[Depends(require_authorized_client)])
async def interrogate_onvif_endpoint(
    payload: ONVIFInterrogateRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Query ONVIF GetDeviceInformation, GetCapabilities, and GetProfiles on a target IP."""
    res = await interrogate_onvif_device(
        ip_address=payload.ip_address,
        port=payload.port,
        username=payload.username,
        password=payload.password,
    )
    if res.get("reachable"):
        dev_repo = DeviceRepository(db)
        cam_repo = CameraRepository(db)
        dev = dev_repo.upsert_discovered_device(
            {
                "ip_address": payload.ip_address,
                "manufacturer": res.get("manufacturer"),
                "model": res.get("model"),
                "category": "ONVIF_CAMERA",
                "confidence": "HIGH",
                "classification_evidence": ["Verified via direct ONVIF SOAP interrogation"],
                "onvif_available": True,
                "rtsp_available": True,
                "detected_protocols": ["ONVIF", "HTTP", "RTSP"],
                "discovery_methods": ["ONVIF"],
                "is_online": True,
            }
        )
        cam_repo.upsert_camera(
            device_id=dev.id,
            ip_address=payload.ip_address,
            data={
                "manufacturer": res.get("manufacturer"),
                "model": res.get("model"),
                "firmware_version": res.get("firmware_version"),
                "serial_number": res.get("serial_number"),
                "hardware_id": res.get("hardware_id"),
                "onvif_supported": True,
                "onvif_port": payload.port,
                "onvif_capabilities": res.get("capabilities", {}),
                "media_profiles": res.get("media_profiles", []),
                "rtsp_available": True,
                "requires_auth": res.get("auth_required", False),
            },
        )
    return res

