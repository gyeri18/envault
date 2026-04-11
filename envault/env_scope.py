"""Scope management: restrict visible keys to a named subset."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised for scope-related errors."""


class ScopeManager:
    """Manage named scopes that map to subsets of env keys."""

    _SCOPES_FILE = "scopes.json"

    def __init__(self, config_dir: Path) -> None:
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _scopes_path(self) -> Path:
        return self._config_dir / self._SCOPES_FILE

    def _load(self) -> Dict[str, List[str]]:
        if not self._scopes_path.exists():
            return {}
        return json.loads(self._scopes_path.read_text())

    def _save(self, data: Dict[str, List[str]]) -> None:
        self._scopes_path.write_text(json.dumps(data, indent=2))

    def create(self, scope: str, keys: List[str]) -> None:
        """Create or overwrite a scope with the given key list."""
        if not scope:
            raise ScopeError("Scope name must not be empty.")
        if not keys:
            raise ScopeError("Scope must contain at least one key.")
        data = self._load()
        data[scope] = sorted(set(keys))
        self._save(data)

    def delete(self, scope: str) -> None:
        """Delete a named scope."""
        data = self._load()
        if scope not in data:
            raise ScopeError(f"Scope '{scope}' does not exist.")
        del data[scope]
        self._save(data)

    def get(self, scope: str) -> List[str]:
        """Return the list of keys for a scope."""
        data = self._load()
        if scope not in data:
            raise ScopeError(f"Scope '{scope}' does not exist.")
        return data[scope]

    def list_scopes(self) -> List[str]:
        """Return all defined scope names."""
        return sorted(self._load().keys())

    def apply(
        self, scope: str, env_pairs: Dict[str, str]
    ) -> Dict[str, str]:
        """Return only the env pairs whose keys belong to *scope*."""
        allowed = set(self.get(scope))
        return {k: v for k, v in env_pairs.items() if k in allowed}

    def add_key(self, scope: str, key: str) -> None:
        """Add a key to an existing scope."""
        keys = self.get(scope)
        if key in keys:
            raise ScopeError(f"Key '{key}' is already in scope '{scope}'.")
        keys.append(key)
        data = self._load()
        data[scope] = sorted(keys)
        self._save(data)

    def remove_key(self, scope: str, key: str) -> None:
        """Remove a key from an existing scope."""
        keys = self.get(scope)
        if key not in keys:
            raise ScopeError(f"Key '{key}' is not in scope '{scope}'.")
        keys.remove(key)
        if not keys:
            raise ScopeError("Cannot remove the last key from a scope.")
        data = self._load()
        data[scope] = sorted(keys)
        self._save(data)
