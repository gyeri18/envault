"""Access control for env keys: restrict which keys a given role/user can read."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class AccessError(Exception):
    """Raised on access-control violations or misuse."""


class AccessEntry:
    def __init__(self, role: str, keys: List[str]):
        self.role = role
        self.keys = sorted(set(keys))

    def __str__(self) -> str:
        return f"{self.role}: {', '.join(self.keys)}"

    def to_dict(self) -> dict:
        return {"role": self.role, "keys": self.keys}

    @classmethod
    def from_dict(cls, data: dict) -> "AccessEntry":
        return cls(data["role"], data["keys"])


class AccessManager:
    """Manage per-role key access policies stored in the envault config dir."""

    def __init__(self, config_dir: Optional[Path] = None):
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _access_path(self) -> Path:
        return self._config_dir / "access.json"

    def _load(self) -> Dict[str, List[str]]:
        p = self._access_path()
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    def _save(self, data: Dict[str, List[str]]) -> None:
        self._access_path().write_text(json.dumps(data, indent=2))

    def grant(self, role: str, keys: List[str]) -> AccessEntry:
        """Grant *role* access to *keys* (merges with existing grants)."""
        if not role:
            raise AccessError("Role name must not be empty.")
        if not keys:
            raise AccessError("Key list must not be empty.")
        data = self._load()
        existing = set(data.get(role, []))
        existing.update(keys)
        data[role] = sorted(existing)
        self._save(data)
        return AccessEntry(role, data[role])

    def revoke(self, role: str, keys: List[str]) -> AccessEntry:
        """Remove *keys* from *role*'s allowed set."""
        data = self._load()
        if role not in data:
            raise AccessError(f"Role '{role}' not found.")
        remaining = [k for k in data[role] if k not in keys]
        data[role] = remaining
        self._save(data)
        return AccessEntry(role, remaining)

    def can_access(self, role: str, key: str) -> bool:
        """Return True if *role* is allowed to read *key*."""
        data = self._load()
        return key in data.get(role, [])

    def allowed_keys(self, role: str) -> List[str]:
        """Return the list of keys *role* may access."""
        return list(self._load().get(role, []))

    def list_roles(self) -> List[str]:
        """Return all defined roles."""
        return sorted(self._load().keys())

    def delete_role(self, role: str) -> None:
        """Remove a role and all its grants."""
        data = self._load()
        if role not in data:
            raise AccessError(f"Role '{role}' not found.")
        del data[role]
        self._save(data)
