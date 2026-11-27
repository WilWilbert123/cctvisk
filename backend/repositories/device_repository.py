"""Repository for Device CRUD, filtering, and upsert operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from backend.models.device import Device


class DeviceRepository:
    """Data access layer for Device records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, device_id: int) -> Device | None:
        stmt = (
            select(Device)
            .options(joinedload(Device.camera), joinedload(Device.nvr))
            .where(Device.id == device_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_ip(self, ip_address: str) -> Device | None:
        stmt = (
            select(Device)
            .options(joinedload(Device.camera), joinedload(Device.nvr))
            .where(Device.ip_address == ip_address)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_devices(
        self,
        search: str | None = None,
        category: str | None = None,
        is_online: bool | None = None,
        confidence: str | None = None,
        sort_by: str = "ip_address",
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[Device], int]:
        stmt = select(Device).options(joinedload(Device.camera), joinedload(Device.nvr))

        if search and search.strip():
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Device.ip_address.ilike(q),
                    Device.mac_address.ilike(q),
                    Device.manufacturer.ilike(q),
                    Device.model.ilike(q),
                    Device.hostname.ilike(q),
                    Device.label.ilike(q),
                )
            )

        if category and category.upper() != "ALL":
            cat_upper = category.upper()
            if cat_upper in ("CAMERA", "IP_CAMERA", "ONVIF_CAMERA"):
                stmt = stmt.where(Device.category.in_(["CAMERA", "ONVIF_CAMERA"]))
            elif cat_upper in ("NVR_DVR", "NVR", "DVR"):
                stmt = stmt.where(Device.category.in_(["NVR", "DVR"]))
            elif cat_upper in ("NETWORK_INFRASTRUCTURE", "ROUTER", "NETWORK_DEVICE"):
                stmt = stmt.where(Device.category.in_(["ROUTER", "NETWORK_DEVICE"]))
            elif cat_upper in ("WORKSTATION_MOBILE", "COMPUTER", "NAS"):
                stmt = stmt.where(Device.category.in_(["COMPUTER", "NAS"]))
            else:
                stmt = stmt.where(Device.category == cat_upper)

        if is_online is not None:
            stmt = stmt.where(Device.is_online == is_online)

        if confidence and confidence.upper() != "ALL":
            stmt = stmt.where(Device.confidence == confidence.upper())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(self.session.execute(count_stmt).scalar() or 0)

        sort_map: dict[str, Any] = {
            "ip_address": Device.ip_address.asc(),
            "last_seen": Device.last_seen.desc(),
            "category": Device.category.asc(),
            "manufacturer": Device.manufacturer.asc(),
            "confidence": Device.confidence.asc(),
        }
        stmt = stmt.order_by(sort_map.get(sort_by, Device.ip_address.asc()))
        stmt = stmt.offset(max(0, (page - 1) * page_size)).limit(page_size)

        items = list(self.session.execute(stmt).scalars().unique().all())
        return items, total

    def get_all(self) -> list[Device]:
        stmt = select(Device).options(joinedload(Device.camera), joinedload(Device.nvr)).order_by(Device.id.asc())
        return list(self.session.execute(stmt).scalars().unique().all())

    def get_monitored_devices(self) -> list[Device]:
        stmt = select(Device).where(Device.is_monitored.is_(True)).order_by(Device.id.asc())
        return list(self.session.execute(stmt).scalars().all())

    def upsert_discovered_device(self, data: dict[str, Any]) -> Device:
        ip_address = data["ip_address"]
        now = datetime.now(timezone.utc)
        device = self.get_by_ip(ip_address)

        if device is None:
            device = Device(
                ip_address=ip_address,
                mac_address=data.get("mac_address"),
                manufacturer=data.get("manufacturer"),
                model=data.get("model"),
                hostname=data.get("hostname"),
                label=data.get("label"),
                category=data.get("category", "UNKNOWN"),
                confidence=data.get("confidence", "UNKNOWN"),
                classification_evidence=data.get("classification_evidence", []),
                open_ports=data.get("open_ports", []),
                service_banners=data.get("service_banners", {}),
                detected_protocols=data.get("detected_protocols", []),
                discovery_methods=data.get("discovery_methods", []),
                onvif_available=bool(data.get("onvif_available", False)),
                rtsp_available=bool(data.get("rtsp_available", False)),
                is_online=bool(data.get("is_online", True)),
                is_monitored=bool(data.get("is_monitored", True)),
                is_manual=bool(data.get("is_manual", False)),
                latency_ms=data.get("latency_ms"),
                notes=data.get("notes"),
                last_seen=now,
            )
            self.session.add(device)
        else:
            if data.get("mac_address"):
                device.mac_address = data["mac_address"]
            if data.get("manufacturer") and data["manufacturer"] != "UNKNOWN":
                device.manufacturer = data["manufacturer"]
            if data.get("model"):
                device.model = data["model"]
            if data.get("hostname"):
                device.hostname = data["hostname"]
            if data.get("category") and (
                device.category == "UNKNOWN" or data.get("confidence") in ("HIGH", "MEDIUM")
            ):
                device.category = data["category"]
            if data.get("confidence"):
                device.confidence = data["confidence"]
            if data.get("classification_evidence"):
                merged_ev = list(
                    dict.fromkeys(
                        (device.classification_evidence or []) + data["classification_evidence"]
                    )
                )
                device.classification_evidence = merged_ev
            if data.get("open_ports") is not None:
                merged_ports = sorted(set((device.open_ports or []) + data["open_ports"]))
                device.open_ports = merged_ports
            if data.get("service_banners"):
                banners = dict(device.service_banners or {})
                banners.update(data["service_banners"])
                device.service_banners = banners
            if data.get("detected_protocols"):
                device.detected_protocols = sorted(
                    set((device.detected_protocols or []) + data["detected_protocols"])
                )
            if data.get("discovery_methods"):
                device.discovery_methods = sorted(
                    set((device.discovery_methods or []) + data["discovery_methods"])
                )
            if data.get("onvif_available"):
                device.onvif_available = True
            if data.get("rtsp_available"):
                device.rtsp_available = True
            if data.get("latency_ms") is not None:
                device.latency_ms = data["latency_ms"]
            device.is_online = bool(data.get("is_online", True))
            device.last_seen = now

        self.session.commit()
        self.session.refresh(device)
        return device

    def update_device(self, device: Device, updates: dict[str, Any]) -> Device:
        for key, value in updates.items():
            if value is not None and hasattr(device, key):
                setattr(device, key, value)
        self.session.commit()
        self.session.refresh(device)
        return device

    def delete_device(self, device: Device) -> None:
        self.session.delete(device)
        self.session.commit()

    def get_counts(self) -> dict[str, int]:
        all_devices = self.get_all()
        total = len(all_devices)
        online = sum(1 for d in all_devices if d.is_online)
        offline = total - online
        cameras = sum(1 for d in all_devices if d.category in ("CAMERA", "ONVIF_CAMERA") or d.camera is not None)
        nvrs = sum(1 for d in all_devices if d.category in ("NVR", "DVR") or d.nvr is not None)
        unknown = sum(1 for d in all_devices if d.category == "UNKNOWN")
        monitored = sum(1 for d in all_devices if d.is_monitored)
        return {
            "total_devices": total,
            "online_devices": online,
            "offline_devices": offline,
            "cameras_count": cameras,
            "nvr_dvr_count": nvrs,
            "unknown_devices": unknown,
            "monitored_devices": monitored,
        }
