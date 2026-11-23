"""Repository for Camera CRUD and discovery persistence."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from backend.models.camera import Camera
from backend.models.device import Device
from backend.utils.ip_utils import construct_safe_admin_url


class CameraRepository:
    """Data access layer for Camera entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, camera_id: int) -> Camera | None:
        stmt = select(Camera).options(joinedload(Camera.device)).where(Camera.id == camera_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_device_id(self, device_id: int) -> Camera | None:
        stmt = (
            select(Camera).options(joinedload(Camera.device)).where(Camera.device_id == device_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def resolve_or_create_by_id_or_device(self, identifier: int) -> Camera | None:
        """
        Resolve a Camera by `Camera.id`, fallback to `Camera.device_id == identifier`,
        or auto-provision a Camera record if `Device.id == identifier` exists.
        """
        camera = self.get_by_id(identifier)
        if camera is not None:
            return camera
        camera = self.get_by_device_id(identifier)
        if camera is not None:
            return camera
        dev_stmt = select(Device).where(Device.id == identifier)
        device = self.session.execute(dev_stmt).scalar_one_or_none()
        if device is None:
            return None
        open_ports = device.open_ports or []
        http_port = 8080 if (8080 in open_ports and 80 not in open_ports) else 80
        https_port = 443 if 443 in open_ports else None
        rtsp_port = 8554 if (8554 in open_ports and 554 not in open_ports) else 554
        return self.upsert_camera(
            device_id=device.id,
            ip_address=device.ip_address,
            data={
                "manufacturer": device.manufacturer,
                "model": device.model,
                "onvif_supported": device.onvif_available,
                "rtsp_available": device.rtsp_available or (554 in open_ports),
                "rtsp_port": rtsp_port,
                "http_port": http_port,
                "https_port": https_port,
                "onvif_port": http_port,
                "requires_auth": False,
            },
        )

    def get_by_ip(self, ip_address: str) -> Camera | None:
        stmt = (
            select(Camera)
            .options(joinedload(Camera.device))
            .where(Camera.ip_address == ip_address)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_cameras(self) -> list[Camera]:
        stmt = select(Camera).options(joinedload(Camera.device)).order_by(Camera.id.asc())
        return list(self.session.execute(stmt).scalars().unique().all())

    def delete_camera(self, camera: Camera) -> None:
        self.session.delete(camera)
        self.session.commit()

    def upsert_camera(self, device_id: int, ip_address: str, data: dict[str, Any]) -> Camera:
        camera = self.get_by_device_id(device_id)
        http_port = int(data.get("http_port") or 80)
        https_port = data.get("https_port")
        admin_url = data.get("admin_url") or construct_safe_admin_url(
            ip_address, https_port or http_port, use_https=bool(https_port)
        )

        if camera is None:
            camera = Camera(
                device_id=device_id,
                ip_address=ip_address,
                manufacturer=data.get("manufacturer"),
                model=data.get("model"),
                firmware_version=data.get("firmware_version"),
                serial_number=data.get("serial_number"),
                hardware_id=data.get("hardware_id"),
                onvif_supported=bool(data.get("onvif_supported", False)),
                onvif_port=int(data.get("onvif_port") or 80),
                onvif_xaddrs=data.get("onvif_xaddrs", []),
                onvif_scopes=data.get("onvif_scopes", []),
                onvif_capabilities=data.get("onvif_capabilities", {}),
                media_profiles=data.get("media_profiles", []),
                rtsp_available=bool(data.get("rtsp_available", False)),
                rtsp_port=int(data.get("rtsp_port") or 554),
                rtsp_path=data.get("rtsp_path"),
                http_port=http_port,
                https_port=https_port,
                snapshot_path=data.get("snapshot_path"),
                admin_url=admin_url,
                requires_auth=bool(data.get("requires_auth", True)),
                stream_notes=data.get("stream_notes"),
            )
            self.session.add(camera)
        else:
            camera.ip_address = ip_address
            for field in (
                "manufacturer",
                "model",
                "firmware_version",
                "serial_number",
                "hardware_id",
                "rtsp_path",
                "snapshot_path",
                "stream_notes",
            ):
                if data.get(field):
                    setattr(camera, field, data[field])
            if data.get("onvif_supported"):
                camera.onvif_supported = True
            if data.get("onvif_port"):
                camera.onvif_port = int(data["onvif_port"])
            if data.get("onvif_xaddrs"):
                camera.onvif_xaddrs = data["onvif_xaddrs"]
            if data.get("onvif_scopes"):
                camera.onvif_scopes = data["onvif_scopes"]
            if data.get("onvif_capabilities"):
                camera.onvif_capabilities = data["onvif_capabilities"]
            if data.get("media_profiles"):
                camera.media_profiles = data["media_profiles"]
            if data.get("rtsp_available"):
                camera.rtsp_available = True
            if data.get("rtsp_port"):
                camera.rtsp_port = int(data["rtsp_port"])
            if data.get("http_port"):
                camera.http_port = int(data["http_port"])
            if data.get("https_port") is not None:
                camera.https_port = data["https_port"]
            camera.admin_url = admin_url

        self.session.commit()
        self.session.refresh(camera)
        return camera

