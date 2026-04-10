"""Manage key aliases — map short alias names to full env var keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.exceptions import EnvaultError


class AliasError(EnvaultError):
    """Raised for alias-related errors."""


class AliasManager:
    """Store and resolve per-project key aliases."""

    _FILENAME = "aliases.json"

    def __init__(self, config_dir: str | Path) -> None:
        self._config_dir = Path(config_dir)
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._config_dir / self._FILENAME

    # ------------------------------------------------------------------
    def _load(self) -> Dict[str, str]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def _save(self, data: Dict[str, str]) -> None:
        self._path.write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------
    def add(self, alias: str, key: str) -> None:
        """Register *alias* as a shorthand for *key*."""
        if not alias or not key:
            raise AliasError("Alias and key must be non-empty strings.")
        data = self._load()
        if alias in data:
            raise AliasError(
                f"Alias '{alias}' already exists (points to '{data[alias]}'). "
                "Remove it first."
            )
        data[alias] = key
        self._save(data)

    def remove(self, alias: str) -> None:
        """Delete an alias."""
        data = self._load()
        if alias not in data:
            raise AliasError(f"Alias '{alias}' not found.")
        del data[alias]
        self._save(data)

    def resolve(self, alias: str) -> str:
        """Return the key that *alias* maps to, or raise AliasError."""
        data = self._load()
        if alias not in data:
            raise AliasError(f"Alias '{alias}' not found.")
        return data[alias]

    def list_aliases(self) -> List[Dict[str, str]]:
        """Return all aliases sorted by name."""
        data = self._load()
        return [{"alias": a, "key": k} for a, k in sorted(data.items())]

    def rename(self, old_alias: str, new_alias: str) -> None:
        """Rename an existing alias without changing its target key."""
        data = self._load()
        if old_alias not in data:
            raise AliasError(f"Alias '{old_alias}' not found.")
        if new_alias in data:
            raise AliasError(f"Alias '{new_alias}' already exists.")
        data[new_alias] = data.pop(old_alias)
        self._save(data)
