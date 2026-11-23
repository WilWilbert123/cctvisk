"""Devices API routes for listing, filtering, inspecting, registering, updating, and deleting LAN devices."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_authorized_client
from backend.core.constants import ConfidenceLevel
from backend.core.exceptions import ResourceNotFoundError
from backend.repositories.camera_repository import CameraRepository
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.monitoring_repository import MonitoringRepository
from backend.repositories.nvr_repository import NVRRepository
from backend.repositories.recovery_repository import RecoveryRepository
from backend.schemas.device import DeviceCreateRequest, DeviceUpdateRequest
from backend.services.cameras.camera_info import format_camera_details
from backend.services.nvr.nvr_info import format_nvr_details
from backend.services.ports.service_mapper import map_open_ports_to_services
from backend.utils.mac_utils import normalize_mac

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
    dependencies=[Depends(require_authorized_client)],
)


def _serialize_device(device: Any, vault_ids: set[int]) -> dict[str, Any]:
    return {
        "id": device.id,
        "ip_address": device.ip_address,
        "mac_address": device.mac_address,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "hostname": device.hostname,
        "label": device.label,
        "category": device.category,
        "confidence": device.confidence,
        "classification_evidence": list(device.classification_evidence or []),
        "open_ports": list(device.open_ports or []),
        "service_banners": dict(device.service_banners or {}),
        "detected_protocols": list(device.detected_protocols or []),
        "discovery_methods": list(device.discovery_methods or []),
        "onvif_available": device.onvif_available,
        "rtsp_available": device.rtsp_available,
        "is_online": device.is_online,
        "is_monitored": device.is_monitored,
        "is_favorite": device.is_favorite,
        "is_manual": device.is_manual,
        "latency_ms": device.latency_ms,
        "notes": device.notes,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
        "camera_id": device.camera.id if device.camera else None,
        "nvr_id": device.nvr.id if device.nvr else None,
        "has_saved_credentials": device.id in vault_ids,
    }


@router.get("")
def list_devices(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    is_online: bool | None = Query(default=None),
    confidence: str | None = Query(default=None),
    sort_by: str = Query(default="ip_address"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List discovered and registered devices with filtering, sorting, and pagination."""
    dev_repo = DeviceRepository(db)
    rec_repo = RecoveryRepository(db)
    vault_ids = rec_repo.list_vault_device_ids()
    items, total = dev_repo.list_devices(
        search=search,
        category=category,
        is_online=is_online,
        confidence=confidence,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [_serialize_device(d, vault_ids) for d in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{device_id}")
def get_device_detail(device_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return full device details including open services, camera/NVR links, and recent monitoring records."""
    dev_repo = DeviceRepository(db)
    mon_repo = MonitoringRepository(db)
    rec_repo = RecoveryRepository(db)

    device = dev_repo.get_by_id(device_id)
    if not device:
        raise ResourceNotFoundError("Device", device_id)

    vault_ids = rec_repo.list_vault_device_ids()
    base = _serialize_device(device, vault_ids)
    base["services"] = map_open_ports_to_services(device.open_ports or [])
    base["camera"] = (
        format_camera_details(device.camera, has_saved_credentials=device.id in vault_ids)
        if device.camera
        else None
    )
    base["nvr"] = format_nvr_details(device.nvr) if device.nvr else None
    mon_records = mon_repo.list_for_device(device.id, limit=25)
    base["monitoring_records"] = [
        {
            "id": r.id,
            "is_online": r.is_online,
            "status_changed": r.status_changed,
            "latency_ms": r.latency_ms,
            "probe_method": r.probe_method,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
        }
        for r in mon_records
    ]
    return base


@router.post("", status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Manually register a local network device."""
    dev_repo = DeviceRepository(db)
    cam_repo = CameraRepository(db)
    nvr_repo = NVRRepository(db)
    rec_repo = RecoveryRepository(db)

    cat = payload.category.upper()
    device = dev_repo.upsert_discovered_device(
        {
            "ip_address": payload.ip_address,
            "mac_address": normalize_mac(payload.mac_address),
            "label": payload.label,
            "category": cat,
            "manufacturer": payload.manufacturer,
            "model": payload.model,
            "hostname": payload.hostname,
            "confidence": ConfidenceLevel.HIGH.value,
            "classification_evidence": ["Manually registered by user"],
            "discovery_methods": ["MANUAL"],
            "is_online": True,
            "is_manual": True,
            "notes": payload.notes,
        }
    )
    if cat in ("CAMERA", "ONVIF_CAMERA"):
        cam_repo.upsert_camera(
            device.id,
            device.ip_address,
            {
                "manufacturer": payload.manufacturer,
                "model": payload.model,
                "onvif_supported": cat == "ONVIF_CAMERA",
                "rtsp_available": True,
            },
        )
    elif cat in ("NVR", "DVR"):
        nvr_repo.upsert_nvr(
            device.id,
            device.ip_address,
            {
                "recorder_type": cat,
                "manufacturer": payload.manufacturer,
                "model": payload.model,
            },
        )
    db.refresh(device)
    return _serialize_device(device, rec_repo.list_vault_device_ids())


@router.patch("/{device_id}")
def update_device(
    device_id: int, payload: DeviceUpdateRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Update device label, category, notes, favorite status, or monitoring toggle."""
    dev_repo = DeviceRepository(db)
    cam_repo = CameraRepository(db)
    nvr_repo = NVRRepository(db)
    rec_repo = RecoveryRepository(db)

    device = dev_repo.get_by_id(device_id)
    if not device:
        raise ResourceNotFoundError("Device", device_id)

    updates = payload.model_dump(exclude_unset=True)
    updated = dev_repo.update_device(device, updates)
    if updated.category in ("CAMERA", "ONVIF_CAMERA") and not updated.camera:
        cam_repo.upsert_camera(
            updated.id,
            updated.ip_address,
            {
                "manufacturer": updated.manufacturer,
                "model": updated.model,
                "onvif_supported": updated.category == "ONVIF_CAMERA",
                "rtsp_available": True,
            },
        )
    elif updated.category in ("NVR", "DVR") and not updated.nvr:
        nvr_repo.upsert_nvr(
            updated.id,
            updated.ip_address,
            {
                "recorder_type": updated.category,
                "manufacturer": updated.manufacturer,
                "model": updated.model,
            },
        )
    db.refresh(updated)
    return _serialize_device(updated, rec_repo.list_vault_device_ids())


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete a device and its linked records."""
    dev_repo = DeviceRepository(db)
    device = dev_repo.get_by_id(device_id)
    if not device:
        raise ResourceNotFoundError("Device", device_id)
    dev_repo.delete_device(device)
    return {"deleted": True, "device_id": device_id}

