"""Vault manager: high-level API for encrypting/decrypting .env files."""

from pathlib import Path
from typing import Optional

from envault.crypto import CryptoManager
from envault.storage import StorageManager


class VaultManager:
    """Coordinates crypto and storage to lock/unlock .env files."""

    ENV_EXTENSION = ".env"
    VAULT_EXTENSION = ".env.vault"

    def __init__(self, config_dir: Optional[Path] = None):
        self.crypto = CryptoManager()
        self.storage = StorageManager(config_dir)

    def lock(self, project: str, env_path: Path, password: Optional[str] = None) -> Path:
        """Encrypt a .env file and store it as <name>.env.vault."""
        if not env_path.exists():
            raise FileNotFoundError(f".env file not found: {env_path}")

        key = self._resolve_key(project, password)
        plaintext = env_path.read_bytes()
        ciphertext = self.crypto.encrypt(plaintext, key)

        vault_path = env_path.with_suffix("").with_suffix("") 
        vault_path = Path(str(env_path) + ".vault")
        vault_path.write_bytes(ciphertext)
        return vault_path

    def unlock(self, project: str, vault_path: Path, password: Optional[str] = None) -> Path:
        """Decrypt a .env.vault file and restore the original .env file."""
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault file not found: {vault_path}")

        key = self._resolve_key(project, password)
        ciphertext = vault_path.read_bytes()
        plaintext = self.crypto.decrypt(ciphertext, key)

        env_path = Path(str(vault_path).removesuffix(".vault"))
        env_path.write_bytes(plaintext)
        return env_path

    def init_project(self, project: str, password: Optional[str] = None) -> bytes:
        """Generate and persist a key for a new project."""
        if password:
            key = self.crypto.derive_key_from_password(password)
        else:
            key = self.crypto.generate_key()
        self.storage.save_project_key(project, key)
        return key

    def _resolve_key(self, project: str, password: Optional[str]) -> bytes:
        if password:
            return self.crypto.derive_key_from_password(password)
        key = self.storage.get_project_key(project)
        if key is None:
            raise KeyError(f"No key found for project '{project}'. Run 'envault init {project}' first.")
        return key
