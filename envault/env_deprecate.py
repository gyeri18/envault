"""Mark .env keys as deprecated with optional replacement hints."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class DeprecateError(Exception):
    """Raised when a deprecation operation fails."""


@dataclass
class DeprecationEntry:
    key: str
    reason: str
    replacement: Optional[str] = None

    def __str__(self) -> str:
        msg = f"{self.key}: {self.reason}"
        if self.replacement:
            msg += f" (use '{self.replacement}' instead)"
        return msg


@dataclass
class DeprecationReport:
    entries: List[DeprecationEntry] = field(default_factory=list)

    @property
    def keys(self) -> List[str]:
        return [e.key for e in self.entries]

    def has(self, key: str) -> bool:
        return key in self.keys


class DeprecateManager:
    def __init__(self, config_dir: Path) -> None:
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _deprecations_path(self) -> Path:
        return self._config_dir / "deprecations.json"

    def _load(self) -> Dict[str, Dict]:
        p = self._deprecations_path()
        if not p.exists():
            return {}
        return json.loads(p.read_text())

    def _save(self, data: Dict[str, Dict]) -> None:
        self._deprecations_path().write_text(json.dumps(data, indent=2))

    def mark(self, key: str, reason: str, replacement: Optional[str] = None) -> DeprecationEntry:
        if not key:
            raise DeprecateError("Key must not be empty.")
        if not reason:
            raise DeprecateError("Reason must not be empty.")
        data = self._load()
        if key in data:
            raise DeprecateError(f"Key '{key}' is already marked as deprecated.")
        data[key] = {"reason": reason, "replacement": replacement}
        self._save(data)
        return DeprecationEntry(key=key, reason=reason, replacement=replacement)

    def unmark(self, key: str) -> None:
        data = self._load()
        if key not in data:
            raise DeprecateError(f"Key '{key}' is not marked as deprecated.")
        del data[key]
        self._save(data)

    def list_deprecated(self) -> DeprecationReport:
        data = self._load()
        entries = [
            DeprecationEntry(key=k, reason=v["reason"], replacement=v.get("replacement"))
            for k, v in sorted(data.items())
        ]
        return DeprecationReport(entries=entries)

    def check(self, keys: List[str]) -> DeprecationReport:
        """Return deprecation entries for any of the given keys that are deprecated."""
        data = self._load()
        entries = [
            DeprecationEntry(key=k, reason=data[k]["reason"], replacement=data[k].get("replacement"))
            for k in keys
            if k in data
        ]
        return DeprecationReport(entries=entries)
