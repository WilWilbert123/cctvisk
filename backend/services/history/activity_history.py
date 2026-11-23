"""Retrieves unified system and recovery audit logs."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from backend.repositories.recovery_repository import RecoveryRepository
from backend.repositories.scan_repository import ScanRepository


def get_activity_history_summary(session: Session, limit: int = 100) -> dict[str, Any]:
    scan_repo = ScanRepository(session)
    rec_repo = RecoveryRepository(session)
    activities = scan_repo.list_activities(limit=limit)
    recoveries = rec_repo.list_records(limit=limit)
    return {
        "activities": activities,
        "recoveries": recoveries,
    }

