"""Key rotation support for envault projects."""

import os
from pathlib import Path
from typing import Optional

from .crypto import CryptoManager
from .storage import StorageManager
from .audit import AuditLog
from .exceptions import KeyNotFoundError, VaultFileNotFoundError, RotationError


class KeyRotationManager:
    """Handles re-encryption of vault files under a new project key."""

    def __init__(
        self,
        storage: StorageManager,
        audit: Optional[AuditLog] = None,
    ) -> None:
        self.storage = storage
        self.crypto = CryptoManager()
        self.audit = audit

    def rotate(
        self,
        project_name: str,
        vault_path: str | Path,
        password: Optional[str] = None,
    ) -> bytes:
        """Rotate the encryption key for *project_name*.

        Decrypts *vault_path* with the current key, generates a fresh key,
        re-encrypts the plaintext, overwrites the vault file, and persists
        the new key.  Returns the new raw key bytes.

        Raises:
            KeyNotFoundError: if no key exists for the project yet.
            VaultFileNotFoundError: if *vault_path* does not exist.
            RotationError: if decryption or re-encryption fails.
        """
        vault_path = Path(vault_path)

        old_key = self.storage.get_project_key(project_name)
        if old_key is None:
            raise KeyNotFoundError(project_name)

        if not vault_path.exists():
            raise VaultFileNotFoundError(str(vault_path))

        try:
            ciphertext = vault_path.read_bytes()
            plaintext = self.crypto.decrypt(ciphertext, old_key)
        except Exception as exc:
            raise RotationError(
                f"Failed to decrypt vault during rotation: {exc}"
            ) from exc

        # Generate (or derive) the replacement key
        if password:
            new_key = self.crypto.derive_key_from_password(password)
        else:
            new_key = self.crypto.generate_key()

        try:
            new_ciphertext = self.crypto.encrypt(plaintext, new_key)
            vault_path.write_bytes(new_ciphertext)
        except Exception as exc:
            raise RotationError(
                f"Failed to re-encrypt vault during rotation: {exc}"
            ) from exc

        self.storage.save_project_key(project_name, new_key)

        if self.audit:
            self.audit.record(
                action="rotate",
                project=project_name,
                details={"vault": str(vault_path)},
            )

        return new_key
