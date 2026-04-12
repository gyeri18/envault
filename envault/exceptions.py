"""Custom exception hierarchy for envault."""
from __future__ import annotations


class EnvaultError(Exception):
    """Base exception for all envault errors."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint

    def __str__(self) -> str:
        base = super().__str__()
        if self.hint:
            return f"{base} (hint: {self.hint})"
        return base


# ---------------------------------------------------------------------------
# Crypto
# ---------------------------------------------------------------------------

class CryptoError(EnvaultError):
    """Generic cryptographic error."""


class DecryptionError(CryptoError):
    """Raised when decryption fails (wrong key, corrupted data, etc.)."""

    def __init__(self, message: str = "Decryption failed", hint: str | None = None) -> None:
        super().__init__(message, hint)


class EncryptionError(CryptoError):
    """Raised when encryption fails."""


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

class StorageError(EnvaultError):
    """Generic storage error."""


class ProjectKeyNotFoundError(StorageError):
    """Raised when a project key cannot be located."""


# ---------------------------------------------------------------------------
# Vault
# ---------------------------------------------------------------------------

class VaultError(EnvaultError):
    """Generic vault error."""


class VaultNotFoundError(VaultError):
    """Raised when the vault file does not exist."""


class VaultAlreadyLockedError(VaultError):
    """Raised when attempting to lock an already-locked vault."""


class VaultNotLockedError(VaultError):
    """Raised when attempting to unlock a vault that is not locked."""


# ---------------------------------------------------------------------------
# Import / Export
# ---------------------------------------------------------------------------

class ImportError(EnvaultError):  # noqa: A001
    """Raised when an import operation fails."""


class ExportError(EnvaultError):
    """Raised when an export operation fails."""


class UnsupportedFormatError(EnvaultError):
    """Raised when an unsupported file format is requested."""


# ---------------------------------------------------------------------------
# Key operations
# ---------------------------------------------------------------------------

class KeyRotationError(EnvaultError):
    """Raised when key rotation fails."""


class DuplicateKeyError(EnvaultError):
    """Raised when a duplicate key is encountered where one is not allowed."""


class MissingKeyError(EnvaultError):
    """Raised when a required key is absent."""


# ---------------------------------------------------------------------------
# Mask
# ---------------------------------------------------------------------------

class MaskError(EnvaultError):
    """Raised when a masking operation fails."""


# ---------------------------------------------------------------------------
# Validation / Schema
# ---------------------------------------------------------------------------

class ValidationError(EnvaultError):
    """Raised when env validation fails."""


class SchemaError(EnvaultError):
    """Raised when a schema file is malformed or missing."""


# ---------------------------------------------------------------------------
# Profile / Scope
# ---------------------------------------------------------------------------

class ProfileError(EnvaultError):
    """Raised on profile-related failures."""


class ScopeError(EnvaultError):
    """Raised on scope-related failures."""
