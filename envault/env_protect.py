"""Protection rules: prevent specific keys from being modified or deleted."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class ProtectError(Exception):
    pass


class ProtectedKeyViolation:
    def __init__(self, key: str, reason: str):
        self.key = key
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"

    def __repr__(self) -> str:
        return f"ProtectedKeyViolation(key={self.key!r}, reason={self.reason!r})"


class ProtectManager:
    def __init__(self, config_dir: str | Path):
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _protect_path(self) -> Path:
        return self._config_dir / "protected_keys.json"

    def _load(self) -> dict:
        p = self._protect_path()
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    def _save(self, data: dict) -> None:
        self._protect_path().write_text(json.dumps(data, indent=2))

    def protect(self, key: str, reason: str = "") -> None:
        if not key:
            raise ProtectError("Key must not be empty.")
        data = self._load()
        if key in data:
            raise ProtectError(f"Key '{key}' is already protected.")
        data[key] = {"reason": reason}
        self._save(data)

    def unprotect(self, key: str) -> None:
        data = self._load()
        if key not in data:
            raise ProtectError(f"Key '{key}' is not protected.")
        del data[key]
        self._save(data)

    def is_protected(self, key: str) -> bool:
        return key in self._load()

    def list_protected(self) -> List[dict]:
        data = self._load()
        return [{"key": k, "reason": v.get("reason", "")} for k, v in sorted(data.items())]

    def check(self, keys: List[str]) -> List[ProtectedKeyViolation]:
        data = self._load()
        violations = []
        for key in keys:
            if key in data:
                reason = data[key].get("reason") or "key is protected"
                violations.append(ProtectedKeyViolation(key, reason))
        return violations
