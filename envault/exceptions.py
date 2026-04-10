"""Custom exception hierarchy for envault."""
from __future__ import annotations

from typing import Optional


class EnvaultError(Exception):
    """Base exception for all envault errors."""

    def __init__(self, message: str, *, hint: Optional[str] = None) -> None:
        super().__init__(message)
        self.hint = hint


# ── Crypto ────────────────────────────────────────────────────────────

class CryptoError(EnvaultError):
    """Generic cryptographic failure."""


class DecryptionError(CryptoError):
    """Raised when decryption fails (wrong key, corrupted data, …)."""

    def __init__(self, message: str = "Decryption failed — wrong key or corrupted data.") -> None:
        super().__init__(message)


# ── Storage ───────────────────────────────────────────────────────────

class StorageError(EnvaultError):
    """Raised for config-directory / persistence failures."""


class ProjectKeyNotFoundError(StorageError):
    """Raised when no key exists for the requested project."""

    def __init__(self, project: str) -> None:
        super().__init__(f"No key found for project {project!r}.")
        self.project = project


# ── Vault ─────────────────────────────────────────────────────────────

class VaultError(EnvaultError):
    """Generic vault operation failure."""


class VaultNotFoundError(VaultError):
    """Raised when the .vault file does not exist."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Vault file not found: {path}")
        self.path = path


class VaultAlreadyLockedError(VaultError):
    """Raised when trying to lock an already-locked vault."""


# ── Snapshot ──────────────────────────────────────────────────────────

class SnapshotError(EnvaultError):
    """Generic snapshot failure."""


class SnapshotAlreadyExistsError(SnapshotError):
    """Raised when a snapshot with the given label already exists."""

    def __init__(self, label: str) -> None:
        super().__init__(f"Snapshot {label!r} already exists.")
        self.label = label


class SnapshotNotFoundError(SnapshotError):
    """Raised when the requested snapshot label cannot be found."""

    def __init__(self, label: str) -> None:
        super().__init__(f"Snapshot {label!r} not found.")
        self.label = label


# ── Rotation ──────────────────────────────────────────────────────────

class RotationError(EnvaultError):
    """Raised when key rotation fails."""


# ── Import / Export ───────────────────────────────────────────────────

class ImportError(EnvaultError):  # noqa: A001
    """Raised when importing an env file fails."""


class ExportError(EnvaultError):
    """Raised when exporting fails."""


# ── Merge ─────────────────────────────────────────────────────────────

class MergeError(EnvaultError):
    """Raised for unresolvable merge conflicts."""


# ── Validation ────────────────────────────────────────────────────────

class ValidationSchemaError(EnvaultError):
    """Raised when a .envschema file cannot be parsed."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Schema error in {path!r}: {reason}")
        self.path = path
        self.reason = reason
