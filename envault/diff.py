"""Diff manager for comparing .env file versions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from envault.exceptions import EnvaultError
from envault.vault import VaultManager


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class DiffManager:
    """Compare current .env file against the locked vault snapshot."""

    def __init__(self, vault: VaultManager) -> None:
        self.vault = vault

    def _parse_env_content(self, content: str) -> Dict[str, str]:
        """Parse raw env content into a key/value dict."""
        result: Dict[str, str] = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
        return result

    def diff(
        self,
        project_name: str,
        env_file_path: str,
        password: Optional[str] = None,
        show_values: bool = False,
    ) -> List[DiffEntry]:
        """Return a list of DiffEntry objects comparing vault vs current file."""
        try:
            unlocked_content = self.vault.unlock(
                project_name, env_file_path, password=password
            )
        except EnvaultError as exc:
            raise EnvaultError(f"Cannot unlock vault for diff: {exc}") from exc

        vault_vars = self._parse_env_content(unlocked_content)

        try:
            with open(env_file_path, "r", encoding="utf-8") as fh:
                current_content = fh.read()
        except OSError as exc:
            raise EnvaultError(f"Cannot read env file '{env_file_path}': {exc}") from exc

        current_vars = self._parse_env_content(current_content)

        entries: List[DiffEntry] = []
        all_keys = set(vault_vars) | set(current_vars)

        for key in sorted(all_keys):
            in_vault = key in vault_vars
            in_current = key in current_vars

            if in_vault and not in_current:
                entries.append(
                    DiffEntry(
                        key=key,
                        status="removed",
                        old_value=vault_vars[key] if show_values else None,
                    )
                )
            elif not in_vault and in_current:
                entries.append(
                    DiffEntry(
                        key=key,
                        status="added",
                        new_value=current_vars[key] if show_values else None,
                    )
                )
            elif vault_vars[key] != current_vars[key]:
                entries.append(
                    DiffEntry(
                        key=key,
                        status="changed",
                        old_value=vault_vars[key] if show_values else None,
                        new_value=current_vars[key] if show_values else None,
                    )
                )
            else:
                entries.append(DiffEntry(key=key, status="unchanged"))

        return entries
