"""Repository for persistent application settings."""

from __future__ import annotations

import json
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.models.settings import AppSetting


class SettingsRepository:
    """Data access layer for AppSetting groups with fallback to config/default_settings.json."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _load_defaults(self) -> dict[str, dict[str, Any]]:
        settings = get_settings()
        default_file = settings.config_dir / "default_settings.json"
        if default_file.exists():
            try:
                return json.loads(default_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "general": {"theme": "system", "auto_refresh_dashboard_seconds": 15},
            "network_scan": {"default_timeout_ms": 800, "max_concurrency": 64},
            "monitoring": {"enabled": True, "interval_seconds": 60, "timeout_ms": 1000},
            "security": {"allow_lan_access": False, "require_token_for_lan": True},
            "streaming": {"max_fps": 15, "jpeg_quality": 5},
        }

    def get_all_settings(self) -> dict[str, dict[str, Any]]:
        defaults = self._load_defaults()
        stmt = select(AppSetting)
        rows = list(self.session.execute(stmt).scalars().all())
        existing_map = {r.category: r.values_json for r in rows}

        merged: dict[str, dict[str, Any]] = {}
        for cat, default_vals in defaults.items():
            if cat in existing_map:
                combined = dict(default_vals)
                combined.update(existing_map[cat])
                merged[cat] = combined
            else:
                merged[cat] = dict(default_vals)

        for cat, vals in existing_map.items():
            if cat not in merged:
                merged[cat] = dict(vals)

        return merged

    def get_category(self, category: str) -> dict[str, Any]:
        all_settings = self.get_all_settings()
        return all_settings.get(category, {})

    def update_category(self, category: str, values: dict[str, Any]) -> dict[str, Any]:
        stmt = select(AppSetting).where(AppSetting.category == category)
        row = self.session.execute(stmt).scalar_one_or_none()
        current = self.get_category(category)
        current.update(values)

        if row is None:
            row = AppSetting(category=category, values_json=current)
            self.session.add(row)
        else:
            row.values_json = current
        self.session.commit()
        self.session.refresh(row)
        return row.values_json

