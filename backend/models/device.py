"""Device SQLAlchemy ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from sqlalchemy import JSON, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.constants import ConfidenceLevel, DeviceCategory
from backend.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.camera import Camera
    from backend.models.monitoring import MonitoringRecord
    from backend.models.nvr import NVR
    from backend.models.recovery import RecoveryRecord


class Device(Base, TimestampMixin):
    """Represents a discovered or manually registered local network device."""

    __tablename__ = "devices"
    __table_args__ = (
        Index("ix_devices_ip_address", "ip_address", unique=True),
        Index("ix_devices_mac_address", "mac_address"),
        Index("ix_devices_category", "category"),
        Index("ix_devices_is_online", "is_online"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    mac_address: Mapped[str | None] = mapped_column(String(32), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(
        String(32), default=DeviceCategory.UNKNOWN.value, nullable=False
    )
    confidence: Mapped[str] = mapped_column(
        String(16), default=ConfidenceLevel.UNKNOWN.value, nullable=False
    )
    classification_evidence: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    open_ports: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    service_banners: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    detected_protocols: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    discovery_methods: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    onvif_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rtsp_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_monitored: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column( nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    camera: Mapped["Camera | None"] = relationship(
        "Camera", back_populates="device", uselist=False, cascade="all, delete-orphan"
    )
    nvr: Mapped["NVR | None"] = relationship(
        "NVR", back_populates="device", uselist=False, cascade="all, delete-orphan"
    )
    monitoring_records: Mapped[list["MonitoringRecord"]] = relationship(
        "MonitoringRecord", back_populates="device", cascade="all, delete-orphan"
    )
    recovery_records: Mapped[list["RecoveryRecord"]] = relationship(
        "RecoveryRecord", back_populates="device", cascade="all, delete-orphan"
    )

