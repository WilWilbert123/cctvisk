"""High-level Camera Manager coordinating repository persistence, Vault credentials, and Live Streaming."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from backend.core.constants import ConfidenceLevel, DeviceCategory
from backend.core.exceptions import ResourceNotFoundError
from backend.repositories.camera_repository import CameraRepository
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.recovery_repository import RecoveryRepository
from backend.repositories.scan_repository import ScanRepository
from backend.services.cameras.camera_connection import (
    negotiate_camera_connection,
    stream_registry,
)
from backend.services.cameras.camera_info import format_camera_details
from backend.services.recovery.credential_vault import CredentialVaultService
from backend.utils.ip_utils import validate_authorized_ip


class CameraManagerService:
    """Service managing discovered and manually registered CCTV cameras and live connections."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.camera_repo = CameraRepository(session)
        self.device_repo = DeviceRepository(session)
        self.recovery_repo = RecoveryRepository(session)
        self.scan_repo = ScanRepository(session)
        self.vault = CredentialVaultService(session)

    def list_cameras(self) -> list[dict[str, Any]]:
        cameras = self.camera_repo.list_cameras()
        vault_device_ids = self.recovery_repo.list_vault_device_ids()
        results: list[dict[str, Any]] = []
        for cam in cameras:
            has_cred = cam.device_id in vault_device_ids
            cred_obj = self.recovery_repo.get_vault_credential(cam.device_id) if has_cred else None
            results.append(
                format_camera_details(
                    cam,
                    has_saved_credentials=has_cred,
                    saved_username=cred_obj.username if cred_obj else None,
                    stream_active=stream_registry.is_active(cam.id),
                )
            )
        return results

    def get_camera(self, camera_id: int) -> dict[str, Any]:
        cam = self.camera_repo.resolve_or_create_by_id_or_device(camera_id)
        if not cam:
            raise ResourceNotFoundError("Camera", camera_id)
        cred_obj = self.recovery_repo.get_vault_credential(cam.device_id)
        return format_camera_details(
            cam,
            has_saved_credentials=cred_obj is not None,
            saved_username=cred_obj.username if cred_obj else None,
            stream_active=stream_registry.is_active(cam.id),
        )

    def create_manual_camera(self, payload: dict[str, Any]) -> dict[str, Any]:
        valid_ip = validate_authorized_ip(payload["ip_address"])
        open_ports = sorted(
            {
                int(payload.get("http_port") or 80),
                int(payload.get("rtsp_port") or 554),
                int(payload.get("onvif_port") or 80),
            }
        )
        device = self.device_repo.upsert_discovered_device(
            {
                "ip_address": valid_ip,
                "label": payload.get("label"),
                "manufacturer": payload.get("manufacturer"),
                "model": payload.get("model"),
                "category": DeviceCategory.CAMERA.value,
                "confidence": ConfidenceLevel.HIGH.value,
                "classification_evidence": ["Manually registered CCTV camera by administrator"],
                "open_ports": open_ports,
                "detected_protocols": ["HTTP", "RTSP"],
                "discovery_methods": ["MANUAL"],
                "rtsp_available": True,
                "is_online": True,
                "is_manual": True,
                "notes": payload.get("notes"),
            }
        )
        cam = self.camera_repo.upsert_camera(
            device_id=device.id,
            ip_address=valid_ip,
            data={
                "manufacturer": payload.get("manufacturer"),
                "model": payload.get("model"),
                "rtsp_port": payload.get("rtsp_port", 554),
                "http_port": payload.get("http_port", 80),
                "onvif_port": payload.get("onvif_port", 80),
                "rtsp_path": payload.get("rtsp_path") or "/Streaming/Channels/101",
                "rtsp_available": True,
            },
        )
        if payload.get("save_credentials") and payload.get("username") and payload.get("password"):
            self.vault.save_credentials(
                device_id=device.id,
                username=payload["username"],
                password=payload["password"],
                service_port=int(payload.get("rtsp_port") or 554),
                notes="Saved during manual camera registration",
                explicit_user_consent=True,
            )

        self.scan_repo.log_activity(
            event_type="camera_registered",
            title="Camera Registered",
            message=f"Camera at {valid_ip} registered for management and live viewing.",
            level="info",
            metadata_json={"camera_id": cam.id, "ip_address": valid_ip},
        )
        return self.get_camera(cam.id)

    def update_camera(self, camera_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        cam = self.camera_repo.resolve_or_create_by_id_or_device(camera_id)
        if not cam:
            raise ResourceNotFoundError("Camera", camera_id)

        device = cam.device
        if device:
            dev_updates = {
                k: updates[k]
                for k in ("label", "manufacturer", "model", "is_favorite", "notes")
                if k in updates and updates[k] is not None
            }
            if dev_updates:
                self.device_repo.update_device(device, dev_updates)

        self.camera_repo.upsert_camera(cam.device_id, cam.ip_address, updates)
        return self.get_camera(cam.id)

    def delete_camera(self, camera_id: int) -> dict[str, Any]:
        cam = self.camera_repo.get_by_id(camera_id) or self.camera_repo.get_by_device_id(camera_id)
        if not cam:
            raise ResourceNotFoundError("Camera", camera_id)
        ip_addr = cam.ip_address
        stream_registry.stop(cam.id)
        self.camera_repo.delete_camera(cam)
        return {"deleted": True, "camera_id": camera_id, "ip_address": ip_addr}

    async def connect_camera_live(
        self, camera_id: int, req_data: dict[str, Any]
    ) -> dict[str, Any]:
        cam = self.camera_repo.resolve_or_create_by_id_or_device(camera_id)
        if not cam:
            raise ResourceNotFoundError("Camera", camera_id)

        username = req_data.get("username")
        password = req_data.get("password")

        # If credentials were not passed in the request, check the encrypted Vault
        if not username and password is None:
            vault_creds = self.vault.get_decrypted_credentials_internal(cam.device_id)
            if vault_creds:
                username = vault_creds["username"]
                password = vault_creds["password"]

        rtsp_port = int(req_data.get("rtsp_port") or cam.rtsp_port or 554)
        http_port = int(req_data.get("http_port") or cam.http_port or 80)
        onvif_port = int(req_data.get("onvif_port") or cam.onvif_port or http_port)
        stream_path = req_data.get("stream_path") or cam.rtsp_path

        if req_data.get("save_credentials") and username and password:
            self.vault.save_credentials(
                device_id=cam.device_id,
                username=username,
                password=password,
                service_port=rtsp_port,
                notes="Saved from Live Stream connection dialog",
                explicit_user_consent=True,
            )

        conn_result = await negotiate_camera_connection(
            camera_id=cam.id,
            ip_address=cam.ip_address,
            manufacturer=cam.manufacturer,
            rtsp_port=rtsp_port,
            http_port=http_port,
            onvif_port=onvif_port,
            onvif_supported=cam.onvif_supported,
            stream_path=stream_path,
            channel=int(req_data.get("channel") or 1),
            subtype=int(req_data.get("subtype") or 0),
            username=username,
            password=password,
        )

        # Persist updated ports / stream path / discovered media profiles
        update_fields: dict[str, Any] = {
            "rtsp_port": rtsp_port,
            "http_port": http_port,
            "onvif_port": onvif_port,
        }
        if stream_path:
            update_fields["rtsp_path"] = stream_path
        if conn_result.get("media_profiles"):
            update_fields["media_profiles"] = conn_result["media_profiles"]
            update_fields["onvif_supported"] = True
        self.camera_repo.upsert_camera(cam.device_id, cam.ip_address, update_fields)

        return conn_result

