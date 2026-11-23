"""ScanHistory and ActivityLog SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.base import Base


class ScanHistory(Base):
    """Records per-device discovery snapshot entries associated with a NetworkScan."""

    __tablename__ = "scan_history"
    __table_args__ = (
        Index("ix_scan_history_scan_id", "scan_id"),
        Index("ix_scan_history_ip_address", "ip_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("network_scans.id", ondelete="SET NULL"), nullable=True
    )
    device_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    mac_address: Mapped[str | None] = mapped_column(String(32), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    open_ports: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    discovery_evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class ActivityLog(Base):
    """Audit and system activity event log persisted in SQLite."""

    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_logs_event_type", "event_type"),
        Index("ix_activity_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(16), default="info", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

