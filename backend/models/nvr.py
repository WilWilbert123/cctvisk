"""NVR / DVR SQLAlchemy ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.device import Device


class NVR(Base, TimestampMixin):
    """Represents a Network Video Recorder (NVR) or Digital Video Recorder (DVR)."""

    __tablename__ = "nvrs"
    __table_args__ = (
        Index("ix_nvrs_device_id", "device_id", unique=True),
        Index("ix_nvrs_ip_address", "ip_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    recorder_type: Mapped[str] = mapped_column(String(16), default="NVR", nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)

    http_port: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    rtsp_port: Mapped[int] = mapped_column(Integer, default=554, nullable=False)
    sdk_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onvif_supported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Channels are only populated when verified via ONVIF profiles or authenticated query
    detected_channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channels_info: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    admin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="nvr")

