"""NetworkScan SQLAlchemy ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from sqlalchemy import JSON, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.constants import ScanStatus
from backend.database.base import Base, TimestampMixin


class NetworkScan(Base, TimestampMixin):
    """Represents an executed local network discovery scan session."""

    __tablename__ = "network_scans"
    __table_args__ = (
        Index("ix_network_scans_status", "status"),
        Index("ix_network_scans_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subnet_cidr: Mapped[str] = mapped_column(String(45), nullable=False)
    interface_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    local_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    status: Mapped[str] = mapped_column(
        String(24), default=ScanStatus.RUNNING.value, nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(128), nullable=True)
    total_hosts_probed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    devices_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cameras_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nvrs_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    methods_used: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    scan_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

