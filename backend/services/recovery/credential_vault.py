"""Encrypted Credential Vault service.

Security Guarantees:
- Encrypts passwords using Fernet (AES-128-CBC + HMAC-SHA256) with an external key file.
- Never stores plaintext passwords in SQLite.
- Never logs passwords.
- Never exposes plaintext passwords to any API response or frontend JavaScript.
- Requires explicit_user_consent=True before saving credentials.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.core.exceptions import AppException, SecurityViolationError
from backend.repositories.recovery_repository import RecoveryRepository
from backend.utils.encryption import VaultCipher


class CredentialVaultService:
    """Manages encrypted credential persistence and server-side-only decryption."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = RecoveryRepository(session)
        settings = get_settings()
        self.cipher = VaultCipher(settings.VAULT_KEY_PATH)

    def save_credentials(
        self,
        device_id: int,
        username: str,
        password: str,
        service_port: int = 554,
        notes: str | None = None,
        explicit_user_consent: bool = False,
    ) -> dict[str, Any]:
        """Encrypt and persist credentials after verifying explicit user consent."""
        if not explicit_user_consent:
            raise SecurityViolationError(
                "Explicit user consent is required before saving credentials to the encrypted vault."
            )
        if not username.strip() or not password:
            raise AppException("Username and password must not be empty.")

        encrypted_pw = self.cipher.encrypt(password)
        cred = self.repo.save_vault_credential(
            device_id=device_id,
            username=username.strip(),
            encrypted_password=encrypted_pw,
            service_port=service_port,
            notes=notes,
        )
        return self.get_vault_status(device_id, cred_override=cred)

    def get_vault_status(
        self, device_id: int, cred_override: Any | None = None
    ) -> dict[str, Any]:
        """Return safe metadata about stored credentials without exposing the password."""
        cred = cred_override or self.repo.get_vault_credential(device_id)
        if not cred:
            return {
                "device_id": device_id,
                "has_credentials": False,
                "username": None,
                "service_port": None,
                "notes": None,
                "updated_at": None,
                "encryption_algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)",
                "key_storage_notice": (
                    "Encryption keys are stored outside the SQLite database. If the external key file is lost "
                    "or deleted, encrypted credentials cannot be recovered."
                ),
            }
        return {
            "device_id": device_id,
            "has_credentials": True,
            "username": cred.username,
            "service_port": cred.service_port,
            "notes": cred.notes,
            "updated_at": cred.updated_at.isoformat() if cred.updated_at else None,
            "encryption_algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)",
            "key_storage_notice": (
                "Encryption keys are stored outside the SQLite database. If the external key file is lost "
                "or deleted, encrypted credentials cannot be recovered."
            ),
        }

    def get_decrypted_credentials_internal(self, device_id: int) -> dict[str, Any] | None:
        """
        INTERNAL SERVER-SIDE USE ONLY (e.g., for RTSP/ONVIF stream proxy).
        Never expose the return value of this method in any HTTP/WebSocket response!
        """
        cred = self.repo.get_vault_credential(device_id)
        if not cred:
            return None
        try:
            decrypted_pw = self.cipher.decrypt(cred.encrypted_password)
            return {
                "device_id": device_id,
                "username": cred.username,
                "password": decrypted_pw,
                "service_port": cred.service_port,
            }
        except ValueError:
            return None

    def delete_credentials(self, device_id: int) -> bool:
        """Securely delete stored credentials for a device."""
        return self.repo.delete_vault_credential(device_id)

    def get_vault_health(self) -> dict[str, Any]:
        """Return overall vault encryption key health and count of protected devices."""
        key_meta = self.cipher.key_status()
        protected_ids = self.repo.list_vault_device_ids()
        return {
            **key_meta,
            "protected_devices_count": len(protected_ids),
            "backup_limitation_notice": (
                "Database backups do NOT include the external .vault.key file. "
                "Back up .vault.key separately in a secure location; if the key is lost, "
                "encrypted credentials cannot be decrypted."
            ),
        }

