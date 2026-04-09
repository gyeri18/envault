"""envault — encrypt and manage local .env files with per-project key isolation."""

__version__ = "0.1.0"
__all__ = ["VaultManager", "CryptoManager", "StorageManager"]

from envault.crypto import CryptoManager
from envault.storage import StorageManager
from envault.vault import VaultManager
