"""Password Recovery Assistant and encrypted Credential Vault API routes."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, require_authorized_client
from backend.schemas.recovery import RecoveryRecordCreateRequest, VaultSaveRequest
from backend.services.recovery.credential_vault import CredentialVaultService
from backend.services.recovery.recovery_manager import RecoveryManagerService

router = APIRouter(
    prefix="/recovery",
    tags=["Recovery & Vault"],
    dependencies=[Depends(require_authorized_client)],
)


@router.get("/guides")
def list_manufacturer_recovery_guides(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return all official manufacturer recovery guides."""
    service = RecoveryManagerService(db)
    return {"manufacturers": service.get_all_guides()}


@router.get("/guide/{device_id}")
def get_device_recovery_guide(
    device_id: int,
    manufacturer: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return tailored recovery instructions, reset steps, vault status, and history for a device."""
    service = RecoveryManagerService(db)
    data = service.get_device_recovery_guide(device_id, manual_manufacturer=manufacturer)
    data["history"] = [
        {
            "id": r.id,
            "device_id": r.device_id,
            "ip_address": r.ip_address,
            "manufacturer": r.manufacturer,
            "model": r.model,
            "method_used": r.method_used,
            "status": r.status,
            "notes": r.notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in data["history"]
    ]
    return data


@router.get("/records")
def list_recovery_records(
    device_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List password recovery activity history."""
    service = RecoveryManagerService(db)
    rows = service.list_recovery_history(device_id=device_id)
    items = [
        {
            "id": r.id,
            "device_id": r.device_id,
            "ip_address": r.ip_address,
            "manufacturer": r.manufacturer,
            "model": r.model,
            "method_used": r.method_used,
            "status": r.status,
            "notes": r.notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]
    return {"items": items, "total": len(items)}


@router.post("/records", status_code=status.HTTP_201_CREATED)
def create_recovery_record(
    payload: RecoveryRecordCreateRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Record a password recovery workflow step or completion outcome."""
    service = RecoveryManagerService(db)
    r = service.record_recovery_step(payload.model_dump())
    return {
        "id": r.id,
        "device_id": r.device_id,
        "ip_address": r.ip_address,
        "manufacturer": r.manufacturer,
        "model": r.model,
        "method_used": r.method_used,
        "status": r.status,
        "notes": r.notes,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.post("/vault/credentials", status_code=status.HTTP_201_CREATED)
def save_credentials_to_vault(
    payload: VaultSaveRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Encrypt and save newly configured camera/NVR credentials into the local Vault.
    Requires explicit_user_consent=True. Never returns the plaintext password.
    """
    vault = CredentialVaultService(db)
    return vault.save_credentials(
        device_id=payload.device_id,
        username=payload.username,
        password=payload.password,
        service_port=payload.service_port,
        notes=payload.notes,
        explicit_user_consent=payload.explicit_user_consent,
    )


@router.get("/vault/status/{device_id}")
def get_vault_credential_status(device_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Check whether encrypted credentials exist for a device (never returns the password)."""
    vault = CredentialVaultService(db)
    return vault.get_vault_status(device_id)


@router.delete("/vault/credentials/{device_id}")
def delete_vault_credentials(device_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Securely delete stored credentials for a device."""
    vault = CredentialVaultService(db)
    deleted = vault.delete_credentials(device_id)
    return {"deleted": deleted, "device_id": device_id}

