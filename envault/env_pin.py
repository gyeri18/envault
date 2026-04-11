"""Pin specific env var keys to track required presence across environments."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from envault.exceptions import EnvaultError


class PinError(EnvaultError):
    """Raised when a pin operation fails."""


class PinManager:
    """Manage a list of pinned (required) env var keys for a project."""

    _FILENAME = "pins.json"

    def __init__(self, config_dir: str | Path) -> None:
        self._config_dir = Path(config_dir)
        self._path = self._config_dir / self._FILENAME
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, List[str]]:
        if not self._path.exists():
            return {}
        with self._path.open() as fh:
            return json.load(fh)

    def _save(self, data: Dict[str, List[str]]) -> None:
        with self._path.open("w") as fh:
            json.dump(data, fh, indent=2)

    def pin(self, project: str, key: str) -> None:
        """Mark *key* as required for *project*."""
        if not key:
            raise PinError("Key must not be empty.")
        data = self._load()
        pins = data.setdefault(project, [])
        if key in pins:
            raise PinError(f"Key '{key}' is already pinned for project '{project}'.")
        pins.append(key)
        self._save(data)

    def unpin(self, project: str, key: str) -> None:
        """Remove *key* from the pinned list for *project*."""
        data = self._load()
        pins = data.get(project, [])
        if key not in pins:
            raise PinError(f"Key '{key}' is not pinned for project '{project}'.")
        pins.remove(key)
        if not pins:
            del data[project]
        else:
            data[project] = pins
        self._save(data)

    def list_pins(self, project: str) -> List[str]:
        """Return all pinned keys for *project* (may be empty)."""
        return list(self._load().get(project, []))

    def check(self, project: str, env_keys: List[str]) -> List[str]:
        """Return pinned keys that are missing from *env_keys*."""
        pinned = set(self.list_pins(project))
        present = set(env_keys)
        return sorted(pinned - present)
