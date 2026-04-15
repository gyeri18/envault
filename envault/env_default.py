"""Manage default values for env keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class DefaultError(Exception):
    pass


class DefaultEntry:
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def __str__(self) -> str:
        return f"{self.key}={self.value}"

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value}


class DefaultManager:
    def __init__(self, config_dir: Optional[Path] = None):
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _defaults_path(self) -> Path:
        return self._config_dir / "defaults.json"

    def _load(self) -> Dict[str, str]:
        p = self._defaults_path()
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    def _save(self, data: Dict[str, str]) -> None:
        self._defaults_path().write_text(json.dumps(data, indent=2))

    def set(self, key: str, value: str) -> DefaultEntry:
        if not key.strip():
            raise DefaultError("Key must not be empty.")
        data = self._load()
        data[key] = value
        self._save(data)
        return DefaultEntry(key, value)

    def remove(self, key: str) -> None:
        data = self._load()
        if key not in data:
            raise DefaultError(f"No default registered for key: {key!r}")
        del data[key]
        self._save(data)

    def get(self, key: str) -> Optional[str]:
        return self._load().get(key)

    def list_defaults(self) -> List[DefaultEntry]:
        return [DefaultEntry(k, v) for k, v in sorted(self._load().items())]

    def apply(self, env: Dict[str, str]) -> Dict[str, str]:
        """Return env dict with defaults filled in for missing keys."""
        defaults = self._load()
        result = dict(env)
        for key, value in defaults.items():
            if key not in result or result[key] == "":
                result[key] = value
        return result
