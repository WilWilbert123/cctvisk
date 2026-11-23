"""Repository for RecoveryRecord and VaultCredential persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models.recovery import RecoveryRecord, VaultCredential


class RecoveryRepository:
    """Data access layer for authorized password recovery records and encrypted vault storage."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_record(
        self,
        device_id: int,
        ip_address: str,
        manufacturer: str | None,
        model: str | None,
        method_used: str,
        status: str,
        notes: str | None = None,
    ) -> RecoveryRecord:
        record = RecoveryRecord(
            device_id=device_id,
            ip_address=ip_address,
            manufacturer=manufacturer,
            model=model,
            method_used=method_used,
            status=status,
            notes=notes,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_records(self, device_id: int | None = None, limit: int = 100) -> list[RecoveryRecord]:
        stmt = select(RecoveryRecord).order_by(RecoveryRecord.id.desc()).limit(limit)
        if device_id is not None:
            stmt = stmt.where(RecoveryRecord.device_id == device_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_vault_credential(self, device_id: int) -> VaultCredential | None:
        stmt = select(VaultCredential).where(VaultCredential.device_id == device_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_vault_device_ids(self) -> set[int]:
        stmt = select(VaultCredential.device_id)
        return set(self.session.execute(stmt).scalars().all())

    def save_vault_credential(
        self,
        device_id: int,
        username: str,
        encrypted_password: str,
        service_port: int = 554,
        notes: str | None = None,
    ) -> VaultCredential:
        cred = self.get_vault_credential(device_id)
        if cred is None:
            cred = VaultCredential(
                device_id=device_id,
                username=username,
                encrypted_password=encrypted_password,
                service_port=service_port,
                notes=notes,
            )
            self.session.add(cred)
        else:
            cred.username = username
            cred.encrypted_password = encrypted_password
            cred.service_port = service_port
            cred.notes = notes
        self.session.commit()
        self.session.refresh(cred)
        return cred

    def delete_vault_credential(self, device_id: int) -> bool:
        cred = self.get_vault_credential(device_id)
        if cred is None:
            return False
        self.session.delete(cred)
        self.session.commit()
        return True

