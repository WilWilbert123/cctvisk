"""NVR / DVR API routes."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_authorized_client
from backend.schemas.nvr import NVRChannelDetectRequest, NVRCreateRequest
from backend.services.nvr.nvr_manager import NVRManagerService

router = APIRouter(
    prefix="/nvr",
    tags=["NVR / DVR"],
    dependencies=[Depends(require_authorized_client)],
)


@router.get("")
def list_nvr_devices(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List all discovered or manually registered NVR/DVR recorders."""
    service = NVRManagerService(db)
    items = service.list_nvrs()
    return {"items": items, "total": len(items)}


@router.get("/{nvr_id}")
def get_nvr_device(nvr_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed information for a specific NVR/DVR recorder."""
    service = NVRManagerService(db)
    return service.get_nvr(nvr_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_nvr_device(payload: NVRCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Manually register an NVR or DVR recorder."""
    service = NVRManagerService(db)
    return service.create_manual_nvr(payload.model_dump())


@router.post("/{nvr_id}/detect-channels")
async def detect_nvr_channels(
    nvr_id: int, payload: NVRChannelDetectRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Query verified NVR video channels via ONVIF media profile enumeration."""
    service = NVRManagerService(db)
    return await service.detect_channels(nvr_id, payload.model_dump())

