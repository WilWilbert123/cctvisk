"""RecoveryRecord and VaultCredential SQLAlchemy ORM models."""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.constants import RecoveryStatus
from backend.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.device import Device


class RecoveryRecord(Base, TimestampMixin):
    """Tracks authorized password recovery workflow activity for a camera or NVR."""

    __tablename__ = "recovery_records"
    __table_args__ = (Index("ix_recovery_records_device_id", "device_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    method_used: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=RecoveryStatus.INITIATED.value, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="recovery_records")


class VaultCredential(Base, TimestampMixin):
    """
    Stores encrypted device credentials in SQLite.
    The encryption key resides outside the database in VAULT_KEY_PATH.
    Plaintext passwords are never stored or returned to frontend APIs.
    """

    __tablename__ = "vault_credentials"
    __table_args__ = (Index("ix_vault_credentials_device_id", "device_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    username: Mapped[str] = mapped_column(String(128), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    service_port: Mapped[int] = mapped_column(Integer, default=554, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

