"""Retrieves past network scan sessions and per-scan device snapshots."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from backend.repositories.scan_repository import ScanRepository


def get_scan_history_summary(session: Session, limit: int = 50) -> dict[str, Any]:
    repo = ScanRepository(session)
    scans = repo.list_scans(limit=limit)
    snapshots = repo.list_scan_history(limit=limit * 2)
    return {
        "scans": scans,
        "snapshots": snapshots,
        "total_scans": len(scans),
    }

