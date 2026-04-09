"""
Custom exceptions for the envault CLI tool.

Provides a clear exception hierarchy so callers can catch specific
error conditions without relying on generic built-in exceptions.
"""


class EnvaultError(Exception):
    """Base exception for all envault errors."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Crypto errors
# ---------------------------------------------------------------------------

class CryptoError(EnvaultError):
    """Raised when an encryption or decryption operation fails."""


class DecryptionError(CryptoError):
    """Raised when decryption fails, usually due to a wrong key or corrupted data."""

    def __init__(self, message: str = "Decryption failed: invalid key or corrupted data.") -> None:
        super().__init__(message)


class EncryptionError(CryptoError):
    """Raised when encryption fails unexpectedly."""

    def __init__(self, message: str = "Encryption failed.") -> None:
        super().__init__(message)


# ---------------------------------------------------------------------------
# Storage errors
# ---------------------------------------------------------------------------

class StorageError(EnvaultError):
    """Raised when reading from or writing to the config store fails."""


class ProjectKeyNotFoundError(StorageError):
    """Raised when no encryption key exists for the requested project."""

    def __init__(self, project: str) -> None:
        self.project = project
        super().__init__(f"No key found for project '{project}'. Run 'envault init' first.")


class ConfigDirError(StorageError):
    """Raised when the envault config directory cannot be created or accessed."""

    def __init__(self, path: str, reason: str = "") -> None:
        self.path = path
        detail = f": {reason}" if reason else ""
        super().__init__(f"Cannot access config directory '{path}'{detail}.")


# ---------------------------------------------------------------------------
# Vault errors
# ---------------------------------------------------------------------------

class VaultError(EnvaultError):
    """Raised when a vault-level operation (lock/unlock) fails."""


class VaultNotFoundError(VaultError):
    """Raised when the expected .vault file does not exist."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Vault file not found: '{path}'. Run 'envault lock' to create it.")


class EnvFileNotFoundError(VaultError):
    """Raised when the source .env file is missing during a lock operation."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f".env file not found: '{path}'.")


class ProjectAlreadyInitializedError(VaultError):
    """Raised when 'init' is called on a project that already has a key."""

    def __init__(self, project: str) -> None:
        self.project = project
        super().__init__(
            f"Project '{project}' is already initialized. "
            "Use --force to overwrite the existing key."
        )


# ---------------------------------------------------------------------------
# Audit errors
# ---------------------------------------------------------------------------

class AuditError(EnvaultError):
    """Raised when the audit log cannot be read or written."""
