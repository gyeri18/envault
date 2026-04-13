"""Bulk encrypt all .env files found under a directory."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import VaultManager
from envault.exceptions import EnvaultError


class EncryptAllError(EnvaultError):
    """Raised when a bulk-encrypt operation fails."""


@dataclass
class EncryptAllResult:
    encrypted: List[Path] = field(default_factory=list)
    skipped: List[Path] = field(default_factory=list)
    failed: List[tuple] = field(default_factory=list)  # (path, reason)

    @property
    def ok(self) -> bool:
        return len(self.failed) == 0

    def summary(self) -> str:
        lines = [
            f"Encrypted : {len(self.encrypted)}",
            f"Skipped   : {len(self.skipped)}",
            f"Failed    : {len(self.failed)}",
        ]
        return "\n".join(lines)


class EncryptAllManager:
    """Walk a directory tree and lock every .env file found."""

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        password: Optional[str] = None,
    ) -> None:
        self._config_dir = config_dir
        self._password = password

    def encrypt_all(
        self,
        root: Path,
        pattern: str = "**/.env*",
        skip_already_locked: bool = True,
    ) -> EncryptAllResult:
        """Recursively encrypt env files under *root*."""
        root = Path(root)
        if not root.is_dir():
            raise EncryptAllError(f"Root path is not a directory: {root}")

        result = EncryptAllResult()

        for env_path in sorted(root.glob(pattern)):
            if not env_path.is_file():
                continue

            vault_path = env_path.with_suffix(".vault")

            if skip_already_locked and vault_path.exists():
                result.skipped.append(env_path)
                continue

            try:
                vm = VaultManager(
                    env_file=env_path,
                    config_dir=self._config_dir,
                )
                project_name = str(env_path.relative_to(root)).replace(os.sep, "/")
                vm.init_project(project_name=project_name, password=self._password)
                vm.lock(password=self._password)
                result.encrypted.append(env_path)
            except Exception as exc:  # noqa: BLE001
                result.failed.append((env_path, str(exc)))

        return result
