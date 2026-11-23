"""Settings, database backup, inventory export, and vault configuration API routes."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.dependencies import get_db, require_authorized_client
from backend.database.database import check_db_health
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.scan_repository import ScanRepository
from backend.repositories.settings_repository import SettingsRepository
from backend.schemas.settings import SettingsUpdateRequest
from backend.services.network.interface import get_active_interface
from backend.services.recovery.credential_vault import CredentialVaultService

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
    dependencies=[Depends(require_authorized_client)],
)


@router.get("")
def get_application_settings(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return all application settings, vault status, database health, and LAN access configuration."""
    app_settings = get_settings()
    settings_repo = SettingsRepository(db)
    vault = CredentialVaultService(db)
    active_iface = get_active_interface()
    lan_ip = active_iface.get("ip_address", "127.0.0.1")

    return {
        "settings": settings_repo.get_all_settings(),
        "vault_status": vault.get_vault_health(),
        "database_health": check_db_health(),
        "lan_access": {
            "allow_lan_access": app_settings.ALLOW_LAN_ACCESS,
            "host": app_settings.HOST,
            "port": app_settings.PORT,
            "lan_ip": lan_ip,
            "lan_url": f"http://{lan_ip}:{app_settings.PORT}",
            "pairing_token": app_settings.API_ACCESS_TOKEN,
        },
    }


@router.patch("")
def update_application_settings(
    payload: SettingsUpdateRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Update a settings category and persist to SQLite."""
    settings_repo = SettingsRepository(db)
    updated_cat = settings_repo.update_category(payload.category, payload.values)
    ScanRepository(db).log_activity(
        event_type="settings_updated",
        title="Settings Updated",
        message=f"Updated '{payload.category}' settings.",
        level="info",
    )
    return {
        "category": payload.category,
        "values": updated_cat,
        "settings": settings_repo.get_all_settings(),
    }


@router.post("/backup")
def create_database_backup(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Create a timestamped SQLite database backup in data/backups/."""
    app_settings = get_settings()
    db_path = Path(app_settings.DATABASE_URL.replace("sqlite:///", ""))
    backup_dir = app_settings.data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"cctv_assistant_backup_{timestamp}.db"

    if db_path.exists():
        shutil.copy2(db_path, backup_file)
        size_bytes = backup_file.stat().st_size
    else:
        backup_file.write_bytes(b"")
        size_bytes = 0

    ScanRepository(db).log_activity(
        event_type="database_backup",
        title="Database Backup Created",
        message=f"Saved SQLite backup to {backup_file.name} ({size_bytes} bytes).",
        level="success",
    )
    return {
        "created": True,
        "backup_file": backup_file.name,
        "backup_path": str(backup_file),
        "size_bytes": size_bytes,
        "timestamp": timestamp,
        "vault_notice": "External .vault.key is NOT included in database backups for security.",
    }


@router.post("/export")
def export_device_inventory(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Export discovered devices and cameras inventory (excluding credentials) to data/exports/."""
    app_settings = get_settings()
    export_dir = app_settings.data_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    devices = DeviceRepository(db).get_all()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    export_file = export_dir / f"device_inventory_{timestamp}.json"

    records = [
        {
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "manufacturer": d.manufacturer,
            "model": d.model,
            "hostname": d.hostname,
            "label": d.label,
            "category": d.category,
            "confidence": d.confidence,
            "open_ports": d.open_ports,
            "detected_protocols": d.detected_protocols,
            "onvif_available": d.onvif_available,
            "rtsp_available": d.rtsp_available,
            "is_online": d.is_online,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        }
        for d in devices
    ]
    export_payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_devices": len(records),
        "devices": records,
    }
    export_file.write_text(json.dumps(export_payload, indent=2), encoding="utf-8")

    return {
        "exported": True,
        "export_file": export_file.name,
        "export_path": str(export_file),
        "total_devices": len(records),
        "devices": records,
    }

