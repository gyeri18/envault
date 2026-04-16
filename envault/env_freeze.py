"""Freeze/unfreeze env file keys to prevent accidental modification."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class FreezeError(Exception):
    pass


class FreezeManager:
    def __init__(self, config_dir: str | Path = Path.home() / ".envault") -> None:
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _freeze_path(self) -> Path:
        return self._config_dir / "frozen_keys.json"

    def _load(self) -> dict:
        p = self._freeze_path()
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    def _save(self, data: dict) -> None:
        self._freeze_path().write_text(json.dumps(data, indent=2))

    def freeze(self, key: str, reason: str = "") -> None:
        if not key:
            raise FreezeError("Key must not be empty.")
        data = self._load()
        if key in data:
            raise FreezeError(f"Key '{key}' is already frozen.")
        data[key] = {"reason": reason}
        self._save(data)

    def unfreeze(self, key: str) -> None:
        data = self._load()
        if key not in data:
            raise FreezeError(f"Key '{key}' is not frozen.")
        del data[key]
        self._save(data)

    def is_frozen(self, key: str) -> bool:
        return key in self._load()

    def list_frozen(self) -> List[dict]:
        data = self._load()
        return [{"key": k, "reason": v.get("reason", "")} for k, v in sorted(data.items())]

    def check(self, keys: List[str]) -> List[str]:
        """Return subset of keys that are frozen."""
        data = self._load()
        return [k for k in keys if k in data]
