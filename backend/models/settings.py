"""Settings SQLAlchemy ORM model."""

from __future__ import annotations

from typing import Any
from sqlalchemy import JSON, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.base import Base, TimestampMixin


class AppSetting(Base, TimestampMixin):
    """Key-value configuration group persisted in the SQLite database."""

    __tablename__ = "app_settings"
    __table_args__ = (Index("ix_app_settings_category", "category", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    values_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

