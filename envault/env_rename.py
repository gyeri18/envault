"""Rename or copy environment variable keys within a vault."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.vault import VaultManager
from envault.exceptions import EnvaultError, VaultNotFoundError


class RenameManager:
    """Rename or copy a key inside an encrypted vault."""

    def __init__(
        self,
        vault_path: Path,
        config_dir: Optional[Path] = None,
    ) -> None:
        self.vault_path = Path(vault_path)
        self._vault = VaultManager(vault_path, config_dir=config_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rename(
        self,
        project: str,
        old_key: str,
        new_key: str,
        *,
        password: Optional[str] = None,
        keep_original: bool = False,
    ) -> None:
        """Rename *old_key* to *new_key* inside the vault for *project*.

        Parameters
        ----------
        project:
            Project identifier used to look up the encryption key.
        old_key:
            The existing variable name.
        new_key:
            The desired variable name.
        password:
            Optional password used when the key was derived from a passphrase.
        keep_original:
            When *True* the old key is preserved (copy semantics).
        """
        env = self._vault.unlock(project, password=password)

        if old_key not in env:
            raise EnvaultError(f"Key '{old_key}' not found in vault '{project}'.")
        if new_key in env:
            raise EnvaultError(
                f"Key '{new_key}' already exists in vault '{project}'. "
                "Delete it first or choose a different name."
            )

        env[new_key] = env[old_key]
        if not keep_original:
            del env[old_key]

        self._vault.lock(project, env, password=password)

    def copy(
        self,
        project: str,
        source_key: str,
        dest_key: str,
        *,
        password: Optional[str] = None,
    ) -> None:
        """Copy *source_key* to *dest_key* (keep_original=True shorthand)."""
        self.rename(
            project,
            source_key,
            dest_key,
            password=password,
            keep_original=True,
        )
