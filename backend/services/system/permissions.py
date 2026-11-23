"""Exposes host permission and external binary checks to system services."""

from __future__ import annotations

from typing import Any
from backend.core.permissions import get_permission_summary


def get_system_permissions_report() -> dict[str, Any]:
    """Return detailed permission and binary availability report."""
    return get_permission_summary()

