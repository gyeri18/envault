"""Group related environment variables under named groups for easier management."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class GroupError(Exception):
    """Raised when a group operation fails."""


class GroupManager:
    """Manage named groups of environment variable keys."""

    def __init__(self, config_dir: Path) -> None:
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _groups_path(self) -> Path:
        return self._config_dir / "groups.json"

    def _load(self) -> Dict[str, List[str]]:
        path = self._groups_path()
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    def _save(self, data: Dict[str, List[str]]) -> None:
        self._groups_path().write_text(json.dumps(data, indent=2))

    def create(self, name: str, keys: List[str]) -> None:
        """Create a new group with the given keys."""
        if not name.strip():
            raise GroupError("Group name must not be empty.")
        if not keys:
            raise GroupError("Group must contain at least one key.")
        data = self._load()
        if name in data:
            raise GroupError(f"Group '{name}' already exists.")
        data[name] = sorted(set(k.strip() for k in keys if k.strip()))
        self._save(data)

    def delete(self, name: str) -> None:
        """Delete an existing group."""
        data = self._load()
        if name not in data:
            raise GroupError(f"Group '{name}' does not exist.")
        del data[name]
        self._save(data)

    def get(self, name: str) -> List[str]:
        """Return the keys belonging to a group."""
        data = self._load()
        if name not in data:
            raise GroupError(f"Group '{name}' does not exist.")
        return list(data[name])

    def list_groups(self) -> List[str]:
        """Return all group names sorted alphabetically."""
        return sorted(self._load().keys())

    def add_key(self, name: str, key: str) -> None:
        """Add a key to an existing group."""
        if not key.strip():
            raise GroupError("Key must not be empty.")
        data = self._load()
        if name not in data:
            raise GroupError(f"Group '{name}' does not exist.")
        if key in data[name]:
            raise GroupError(f"Key '{key}' is already in group '{name}'.")
        data[name] = sorted(set(data[name]) | {key})
        self._save(data)

    def remove_key(self, name: str, key: str) -> None:
        """Remove a key from an existing group."""
        data = self._load()
        if name not in data:
            raise GroupError(f"Group '{name}' does not exist.")
        if key not in data[name]:
            raise GroupError(f"Key '{key}' is not in group '{name}'.")
        data[name] = [k for k in data[name] if k != key]
        self._save(data)
