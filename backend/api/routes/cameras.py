"""Cameras API routes including Live Stream negotiation, MJPEG proxy, and JPEG snapshots."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_authorized_client
from backend.core.exceptions import ResourceNotFoundError
from backend.repositories.camera_repository import CameraRepository
from backend.schemas.camera import (
    CameraConnectRequest,
    CameraCreateRequest,
    CameraUpdateRequest,
)
from backend.services.cameras.camera_connection import (
    capture_camera_snapshot,
    stream_mjpeg_frames,
    stream_registry,
)
from backend.services.cameras.camera_manager import CameraManagerService
from backend.services.cameras.camera_status import check_camera_live_status
from backend.services.recovery.credential_vault import CredentialVaultService

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get("", dependencies=[Depends(require_authorized_client)])
def list_cameras(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List all discovered and manually registered CCTV cameras."""
    service = CameraManagerService(db)
    items = service.list_cameras()
    return {"items": items, "total": len(items)}


@router.get("/{camera_id}", dependencies=[Depends(require_authorized_client)])
def get_camera(camera_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed information for a specific CCTV camera."""
    service = CameraManagerService(db)
    return service.get_camera(camera_id)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_authorized_client)])
def create_camera(payload: CameraCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Manually register a local CCTV camera for management and live viewing."""
    service = CameraManagerService(db)
    return service.create_manual_camera(payload.model_dump())


@router.patch("/{camera_id}", dependencies=[Depends(require_authorized_client)])
def update_camera(
    camera_id: int, payload: CameraUpdateRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Update camera label, ports, RTSP stream path, or notes."""
    service = CameraManagerService(db)
    return service.update_camera(camera_id, payload.model_dump(exclude_unset=True))


@router.delete("/{camera_id}", dependencies=[Depends(require_authorized_client)])
def delete_camera(camera_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Remove a camera entry from the CCTV Cameras matrix."""
    service = CameraManagerService(db)
    return service.delete_camera(camera_id)


@router.get("/{camera_id}/status", dependencies=[Depends(require_authorized_client)])
async def probe_camera_status(camera_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Perform a live reachability and RTSP OPTIONS check on the camera."""
    cam = CameraRepository(db).resolve_or_create_by_id_or_device(camera_id)
    if not cam:
        raise ResourceNotFoundError("Camera", camera_id)
    return await check_camera_live_status(
        ip_address=cam.ip_address,
        rtsp_port=cam.rtsp_port or 554,
        http_port=cam.http_port or 80,
    )


@router.post("/{camera_id}/connect", dependencies=[Depends(require_authorized_client)])
async def connect_camera_for_live_view(
    camera_id: int, payload: CameraConnectRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Connect to a discovered or registered camera and negotiate its live RTSP/ONVIF/HTTP stream.
    Returns browser-compatible stream_url (/stream.mjpg) and snapshot_url (/snapshot.jpg).
    """
    service = CameraManagerService(db)
    return await service.connect_camera_live(camera_id, payload.model_dump())


@router.get("/{camera_id}/stream.mjpg", dependencies=[Depends(require_authorized_client)])
async def stream_camera_mjpeg(
    camera_id: int,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Stream live multipart MJPEG video (`multipart/x-mixed-replace; boundary=frame`)
    transcoded in real time from the camera's RTSP stream via FFmpeg or HTTP snapshot fallback.
    """
    cam = CameraRepository(db).resolve_or_create_by_id_or_device(camera_id)
    if not cam:
        raise ResourceNotFoundError("Camera", camera_id)

    vault_creds = CredentialVaultService(db).get_decrypted_credentials_internal(cam.device_id)
    username = vault_creds["username"] if vault_creds else None
    password = vault_creds["password"] if vault_creds else None

    generator = stream_mjpeg_frames(
        camera_id=cam.id,
        ip_address=cam.ip_address,
        manufacturer=cam.manufacturer,
        http_port=cam.http_port or 80,
        rtsp_port=cam.rtsp_port or 554,
        rtsp_path=cam.rtsp_path or "/Streaming/Channels/101",
        username=username,
        password=password,
    )
    return StreamingResponse(
        generator,
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0",
            "Pragma": "no-cache",
            "Connection": "close",
        },
    )


@router.get("/{camera_id}/snapshot.jpg", dependencies=[Depends(require_authorized_client)])
async def get_camera_snapshot(
    camera_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Capture and return a single live JPEG frame from the camera."""
    cam = CameraRepository(db).resolve_or_create_by_id_or_device(camera_id)
    if not cam:
        raise ResourceNotFoundError("Camera", camera_id)

    vault_creds = CredentialVaultService(db).get_decrypted_credentials_internal(cam.device_id)
    username = vault_creds["username"] if vault_creds else None
    password = vault_creds["password"] if vault_creds else None

    jpeg_bytes, source_mode = await capture_camera_snapshot(
        camera_id=cam.id,
        ip_address=cam.ip_address,
        manufacturer=cam.manufacturer,
        http_port=cam.http_port or 80,
        rtsp_port=cam.rtsp_port or 554,
        rtsp_path=cam.rtsp_path or "/Streaming/Channels/101",
        username=username,
        password=password,
    )
    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "X-Snapshot-Source": source_mode,
        },
    )


@router.get("/{camera_id}/stream/status", dependencies=[Depends(require_authorized_client)])
def get_camera_stream_status(camera_id: int) -> dict[str, Any]:
    """Return telemetry for an active camera live stream session."""
    sess = stream_registry.get(camera_id)
    if not sess:
        return {
            "active": False,
            "camera_id": camera_id,
            "frames_served": 0,
            "mode": "idle",
            "last_error": None,
        }
    return {
        "active": sess.active,
        "camera_id": camera_id,
        "ip_address": sess.ip_address,
        "rtsp_url_masked": sess.rtsp_url_masked,
        "frames_served": sess.frames_served,
        "mode": sess.mode,
        "last_error": sess.last_error,
    }


@router.post("/{camera_id}/stream/stop", dependencies=[Depends(require_authorized_client)])
def stop_camera_stream(camera_id: int) -> dict[str, Any]:
    """Stop an active live stream session for a camera."""
    stopped = stream_registry.stop(camera_id)
    return {"stopped": stopped, "camera_id": camera_id}

