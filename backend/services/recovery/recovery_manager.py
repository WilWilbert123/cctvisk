"""High-level Recovery Manager coordinating guides, recovery logs, and Credential Vault."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from backend.core.exceptions import ResourceNotFoundError
from backend.repositories.device_repository import DeviceRepository
from backend.repositories.recovery_repository import RecoveryRepository
from backend.repositories.scan_repository import ScanRepository
from backend.services.recovery.credential_vault import CredentialVaultService
from backend.services.recovery.manufacturer_guide import load_all_recovery_guides
from backend.services.recovery.recovery_workflow import build_recovery_workflow_for_device


class RecoveryManagerService:
    """Coordinates authorized manufacturer recovery guidance, progress tracking, and vault storage."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.device_repo = DeviceRepository(session)
        self.recovery_repo = RecoveryRepository(session)
        self.scan_repo = ScanRepository(session)
        self.vault = CredentialVaultService(session)

    def get_all_guides(self) -> dict[str, dict[str, Any]]:
        return load_all_recovery_guides()

    def get_device_recovery_guide(
        self, device_id: int, manual_manufacturer: str | None = None
    ) -> dict[str, Any]:
        device = self.device_repo.get_by_id(device_id)
        if not device:
            raise ResourceNotFoundError("Device", device_id)

        workflow = build_recovery_workflow_for_device(device, manual_manufacturer=manual_manufacturer)
        vault_status = self.vault.get_vault_status(device_id)
        history = self.recovery_repo.list_records(device_id=device_id, limit=50)

        return {
            **workflow,
            "vault_status": vault_status,
            "history": history,
        }

    def record_recovery_step(self, payload: dict[str, Any]) -> Any:
        device_id = int(payload["device_id"])
        device = self.device_repo.get_by_id(device_id)
        if not device:
            raise ResourceNotFoundError("Device", device_id)

        manufacturer = payload.get("manufacturer") or device.manufacturer
        model = payload.get("model") or device.model
        if manufacturer and not device.manufacturer:
            self.device_repo.update_device(device, {"manufacturer": manufacturer, "model": model})

        record = self.recovery_repo.create_record(
            device_id=device.id,
            ip_address=device.ip_address,
            manufacturer=manufacturer,
            model=model,
            method_used=payload["method_used"],
            status=payload.get("status", "IN_PROGRESS"),
            notes=payload.get("notes"),
        )
        self.scan_repo.log_activity(
            event_type="password_recovery",
            title="Recovery Workflow Updated",
            message=f"Recorded recovery step ({payload['method_used']}) for {device.ip_address} [{record.status}]",
            level="info",
            metadata_json={"device_id": device.id, "ip_address": device.ip_address, "status": record.status},
        )
        return record

    def list_recovery_history(self, device_id: int | None = None, limit: int = 100) -> list[Any]:
        return self.recovery_repo.list_records(device_id=device_id, limit=limit)

