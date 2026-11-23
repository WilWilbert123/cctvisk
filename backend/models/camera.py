"""Camera SQLAlchemy ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.device import Device


class Camera(Base, TimestampMixin):
    """Represents a discovered or registered IP/ONVIF CCTV camera linked to a Device."""

    __tablename__ = "cameras"
    __table_args__ = (
        Index("ix_cameras_device_id", "device_id", unique=True),
        Index("ix_cameras_ip_address", "ip_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hardware_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    onvif_supported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onvif_port: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    onvif_xaddrs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    onvif_scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    onvif_capabilities: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    media_profiles: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    rtsp_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rtsp_port: Mapped[int] = mapped_column(Integer, default=554, nullable=False)
    rtsp_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    http_port: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    https_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snapshot_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stream_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="camera")

