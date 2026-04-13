"""Namespace management for grouping env keys under logical prefixes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class NamespaceError(Exception):
    """Raised on namespace operation failures."""


class NamespaceManager:
    """Manage named namespaces that map to key prefixes."""

    def __init__(self, config_dir: Path) -> None:
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _namespaces_path(self) -> Path:
        return self._config_dir / "namespaces.json"

    def _load(self) -> Dict[str, str]:
        p = self._namespaces_path()
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    def _save(self, data: Dict[str, str]) -> None:
        self._namespaces_path().write_text(json.dumps(data, indent=2))

    def create(self, name: str, prefix: str) -> None:
        """Register a namespace with a key prefix (e.g. 'db' -> 'DB_')."""
        if not name:
            raise NamespaceError("Namespace name must not be empty.")
        if not prefix:
            raise NamespaceError("Prefix must not be empty.")
        data = self._load()
        if name in data:
            raise NamespaceError(f"Namespace '{name}' already exists.")
        data[name] = prefix
        self._save(data)

    def delete(self, name: str) -> None:
        data = self._load()
        if name not in data:
            raise NamespaceError(f"Namespace '{name}' not found.")
        del data[name]
        self._save(data)

    def get_prefix(self, name: str) -> str:
        data = self._load()
        if name not in data:
            raise NamespaceError(f"Namespace '{name}' not found.")
        return data[name]

    def list_namespaces(self) -> List[Dict[str, str]]:
        data = self._load()
        return [{"name": k, "prefix": v} for k, v in sorted(data.items())]

    def keys_in_namespace(
        self, name: str, env_pairs: Dict[str, Optional[str]]
    ) -> Dict[str, Optional[str]]:
        """Return only the env pairs whose key starts with the namespace prefix."""
        prefix = self.get_prefix(name)
        return {k: v for k, v in env_pairs.items() if k.startswith(prefix)}
