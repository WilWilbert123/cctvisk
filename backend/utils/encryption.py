"""Cryptographic encryption utilities for the local Credential Vault (Fernet AES-128-CBC + HMAC-SHA256)."""

from __future__ import annotations

import os
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken


class VaultCipher:
    """
    Manages an external encryption key file stored outside the SQLite database.
    Uses cryptography.fernet.Fernet (AES-128-CBC with PKCS7 padding and HMAC-SHA256 authentication).
    """

    def __init__(self, key_path: str | Path) -> None:
        self.key_path = Path(key_path)
        self._fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        env_key = os.environ.get("VAULT_MASTER_KEY")
        if env_key:
            return env_key.encode("utf-8")

        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            raw = self.key_path.read_bytes().strip()
            if raw:
                return raw

        new_key = Fernet.generate_key()
        self.key_path.write_bytes(new_key)
        try:
            os.chmod(self.key_path, 0o600)
        except OSError:
            pass
        return new_key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return a URL-safe base64 token."""
        if plaintext is None:
            raise ValueError("Cannot encrypt None value.")
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a Fernet token back to plaintext."""
        try:
            raw = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return raw.decode("utf-8")
        except InvalidToken as exc:
            raise ValueError(
                "Failed to decrypt credential vault entry. The external encryption key may have changed."
            ) from exc

    def key_status(self) -> dict[str, str | bool]:
        """Return non-sensitive metadata about the encryption key status."""
        return {
            "key_file_exists": self.key_path.exists(),
            "key_file_path": str(self.key_path),
            "algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)",
            "stored_outside_database": True,
        }

