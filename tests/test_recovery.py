"""Tests for authorized manufacturer recovery guides and encrypted Credential Vault."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session
from backend.core.exceptions import SecurityViolationError
from backend.models.recovery import VaultCredential
from backend.repositories.device_repository import DeviceRepository
from backend.services.recovery.credential_vault import CredentialVaultService
from backend.services.recovery.recovery_manager import RecoveryManagerService


def test_recovery_guide_and_credential_encryption(db_session: Session) -> None:
    dev_repo = DeviceRepository(db_session)
    dev = dev_repo.upsert_discovered_device(
        {
            "ip_address": "192.168.1.64",
            "manufacturer": "Hikvision Digital Technology",
            "model": "DS-2CD2143G2-I",
            "category": "CAMERA",
            "confidence": "HIGH",
        }
    )

    rec_mgr = RecoveryManagerService(db_session)
    guide_res = rec_mgr.get_device_recovery_guide(dev.id)
    assert guide_res["manufacturer_verified"] is True
    assert "SADP" in str(guide_res["guide"]["official_tools"])

    vault = CredentialVaultService(db_session)

    # Saving without explicit_user_consent must be rejected
    with pytest.raises(SecurityViolationError):
        vault.save_credentials(
            device_id=dev.id,
            username="admin",
            password="SuperSecretPassword!99",
            explicit_user_consent=False,
        )

    status_res = vault.save_credentials(
        device_id=dev.id,
        username="admin",
        password="SuperSecretPassword!99",
        service_port=554,
        explicit_user_consent=True,
    )
    assert status_res["has_credentials"] is True
    assert status_res["username"] == "admin"
    assert "SuperSecretPassword!99" not in str(status_res)

    # Verify the raw SQLite column is encrypted ciphertext, never plaintext
    raw_row = db_session.query(VaultCredential).filter_by(device_id=dev.id).one()
    assert raw_row.encrypted_password != "SuperSecretPassword!99"
    assert "SuperSecretPassword!99" not in raw_row.encrypted_password

    # Verify internal server-side decryption works for RTSP stream proxy
    internal = vault.get_decrypted_credentials_internal(dev.id)
    assert internal is not None
    assert internal["password"] == "SuperSecretPassword!99"

    # Verify deletion
    assert vault.delete_credentials(dev.id) is True
    assert vault.get_vault_status(dev.id)["has_credentials"] is False

