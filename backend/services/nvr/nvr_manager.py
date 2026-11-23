"""High-level NVR/DVR Manager service."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from backend.core.constants import ConfidenceLevel
from backend.core.exceptions import ResourceNotFoundError
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.nvr_repository import NVRRepository
from backend.services.nvr.channel_detection import detect_verified_nvr_channels
from backend.services.nvr.nvr_info import format_nvr_details
from backend.utils.ip_utils import validate_authorized_ip


class NVRManagerService:
    """Service coordinating NVR/DVR records and channel verification."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.nvr_repo = NVRRepository(session)
        self.device_repo = DeviceRepository(session)

    def list_nvrs(self) -> list[dict[str, Any]]:
        return [format_nvr_details(n) for n in self.nvr_repo.list_nvrs()]

    def get_nvr(self, nvr_id: int) -> dict[str, Any]:
        nvr = self.nvr_repo.get_by_id(nvr_id)
        if not nvr:
            raise ResourceNotFoundError("NVR/DVR", nvr_id)
        return format_nvr_details(nvr)

    def create_manual_nvr(self, payload: dict[str, Any]) -> dict[str, Any]:
        valid_ip = validate_authorized_ip(payload["ip_address"])
        rec_type = payload.get("recorder_type", "NVR").upper()
        ports = sorted(
            {
                int(payload.get("http_port") or 80),
                int(payload.get("rtsp_port") or 554),
                *( [int(payload["sdk_port"])] if payload.get("sdk_port") else [] ),
            }
        )
        device = self.device_repo.upsert_discovered_device(
            {
                "ip_address": valid_ip,
                "label": payload.get("label"),
                "manufacturer": payload.get("manufacturer"),
                "model": payload.get("model"),
                "category": rec_type,
                "confidence": ConfidenceLevel.HIGH.value,
                "classification_evidence": [f"Manually registered {rec_type} recorder"],
                "open_ports": ports,
                "detected_protocols": ["HTTP", "RTSP"],
                "discovery_methods": ["MANUAL"],
                "rtsp_available": True,
                "is_online": True,
                "is_manual": True,
                "notes": payload.get("notes"),
            }
        )
        nvr = self.nvr_repo.upsert_nvr(
            device_id=device.id,
            ip_address=valid_ip,
            data={
                "recorder_type": rec_type,
                "manufacturer": payload.get("manufacturer"),
                "model": payload.get("model"),
                "http_port": payload.get("http_port", 80),
                "rtsp_port": payload.get("rtsp_port", 554),
                "sdk_port": payload.get("sdk_port"),
                "notes": payload.get("notes"),
            },
        )
        return format_nvr_details(nvr)

    async def detect_channels(self, nvr_id: int, req_data: dict[str, Any]) -> dict[str, Any]:
        nvr = self.nvr_repo.get_by_id(nvr_id)
        if not nvr:
            raise ResourceNotFoundError("NVR/DVR", nvr_id)

        port = int(req_data.get("onvif_port") or nvr.http_port or 80)
        res = await detect_verified_nvr_channels(
            ip_address=nvr.ip_address,
            onvif_port=port,
            username=req_data.get("username"),
            password=req_data.get("password"),
        )
        if res.get("verified"):
            self.nvr_repo.upsert_nvr(
                device_id=nvr.device_id,
                ip_address=nvr.ip_address,
                data={
                    "onvif_supported": True,
                    "detected_channels": res["detected_channels"],
                    "channels_info": res["channels_info"],
                    "manufacturer": res.get("manufacturer"),
                    "model": res.get("model"),
                    "firmware_version": res.get("firmware_version"),
                    "serial_number": res.get("serial_number"),
                },
            )
        return {
            **res,
            "nvr": self.get_nvr(nvr_id),
        }

