"""Repository for NVR/DVR CRUD and discovery persistence."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from backend.models.nvr import NVR
from backend.utils.ip_utils import construct_safe_admin_url


class NVRRepository:
    """Data access layer for NVR/DVR entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, nvr_id: int) -> NVR | None:
        stmt = select(NVR).options(joinedload(NVR.device)).where(NVR.id == nvr_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_device_id(self, device_id: int) -> NVR | None:
        stmt = select(NVR).options(joinedload(NVR.device)).where(NVR.device_id == device_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_nvrs(self) -> list[NVR]:
        stmt = select(NVR).options(joinedload(NVR.device)).order_by(NVR.id.asc())
        return list(self.session.execute(stmt).scalars().unique().all())

    def upsert_nvr(self, device_id: int, ip_address: str, data: dict[str, Any]) -> NVR:
        nvr = self.get_by_device_id(device_id)
        http_port = int(data.get("http_port") or 80)
        admin_url = data.get("admin_url") or construct_safe_admin_url(ip_address, http_port)

        if nvr is None:
            nvr = NVR(
                device_id=device_id,
                ip_address=ip_address,
                recorder_type=data.get("recorder_type", "NVR"),
                manufacturer=data.get("manufacturer"),
                model=data.get("model"),
                firmware_version=data.get("firmware_version"),
                serial_number=data.get("serial_number"),
                http_port=http_port,
                rtsp_port=int(data.get("rtsp_port") or 554),
                sdk_port=data.get("sdk_port"),
                onvif_supported=bool(data.get("onvif_supported", False)),
                detected_channels=data.get("detected_channels"),
                channels_info=data.get("channels_info", []),
                admin_url=admin_url,
                notes=data.get("notes"),
            )
            self.session.add(nvr)
        else:
            nvr.ip_address = ip_address
            for field in (
                "recorder_type",
                "manufacturer",
                "model",
                "firmware_version",
                "serial_number",
                "sdk_port",
                "detected_channels",
                "notes",
            ):
                if data.get(field) is not None:
                    setattr(nvr, field, data[field])
            if data.get("channels_info"):
                nvr.channels_info = data["channels_info"]
            if data.get("onvif_supported"):
                nvr.onvif_supported = True
            nvr.admin_url = admin_url

        self.session.commit()
        self.session.refresh(nvr)
        return nvr

