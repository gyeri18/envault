"""Read-only key management: mark env keys as read-only to prevent accidental modification."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class ReadonlyError(Exception):
    """Raised when a read-only constraint is violated."""


class ReadonlyManager:
    """Manage a set of keys that are marked read-only for a given env file."""

    def __init__(self, config_dir: str | Path) -> None:
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _readonly_path(self) -> Path:
        return self._config_dir / "readonly.json"

    def _load(self) -> dict:
        p = self._readonly_path()
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    def _save(self, data: dict) -> None:
        self._readonly_path().write_text(json.dumps(data, indent=2))

    def mark(self, key: str) -> None:
        """Mark *key* as read-only."""
        if not key:
            raise ReadonlyError("Key must not be empty.")
        data = self._load()
        if key in data:
            raise ReadonlyError(f"Key '{key}' is already marked as read-only.")
        data[key] = True
        self._save(data)

    def unmark(self, key: str) -> None:
        """Remove read-only protection from *key*."""
        data = self._load()
        if key not in data:
            raise ReadonlyError(f"Key '{key}' is not marked as read-only.")
        del data[key]
        self._save(data)

    def is_readonly(self, key: str) -> bool:
        """Return True if *key* is marked read-only."""
        return key in self._load()

    def list_keys(self) -> List[str]:
        """Return a sorted list of all read-only keys."""
        return sorted(self._load().keys())

    def check(self, key: str, new_value: str, env_file: str | Path) -> None:
        """Raise ReadonlyError if *key* is read-only and its value has changed."""
        if not self.is_readonly(key):
            return
        env_path = Path(env_file)
        if not env_path.exists():
            return
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == key and v.strip() != new_value:
                raise ReadonlyError(
                    f"Key '{key}' is read-only and cannot be modified."
                )
