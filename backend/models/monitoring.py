"""MonitoringRecord SQLAlchemy ORM model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.base import Base

if TYPE_CHECKING:
    from backend.models.device import Device


class MonitoringRecord(Base):
    """Stores availability check outcomes and status transitions for monitored devices."""

    __tablename__ = "monitoring_records"
    __table_args__ = (
        Index("ix_monitoring_records_device_id", "device_id"),
        Index("ix_monitoring_records_checked_at", "checked_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status_changed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    probe_method: Mapped[str] = mapped_column(String(32), default="TCP/ICMP", nullable=False)
    event_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    device: Mapped["Device"] = relationship("Device", back_populates="monitoring_records")

