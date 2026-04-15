"""Expiry management for environment variable keys."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class ExpireError(Exception):
    """Raised when an expiry operation fails."""


@dataclass
class ExpiryEntry:
    key: str
    expires_at: str  # ISO-8601 UTC
    note: str = ""

    def __str__(self) -> str:
        note_part = f" ({self.note})" if self.note else ""
        return f"{self.key} expires {self.expires_at}{note_part}"

    def is_expired(self) -> bool:
        expiry = datetime.fromisoformat(self.expires_at)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(tz=timezone.utc) >= expiry

    def to_dict(self) -> dict:
        return {"key": self.key, "expires_at": self.expires_at, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryEntry":
        return cls(key=data["key"], expires_at=data["expires_at"], note=data.get("note", ""))


class ExpireManager:
    def __init__(self, config_dir: Path) -> None:
        self._config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _expiry_path(self) -> Path:
        return self._config_dir / "expiry.json"

    def _load(self) -> Dict[str, ExpiryEntry]:
        path = self._expiry_path()
        if not path.exists():
            return {}
        data = json.loads(path.read_text())
        return {k: ExpiryEntry.from_dict(v) for k, v in data.items()}

    def _save(self, entries: Dict[str, ExpiryEntry]) -> None:
        self._expiry_path().write_text(
            json.dumps({k: v.to_dict() for k, v in entries.items()}, indent=2)
        )

    def set(self, key: str, expires_at: str, note: str = "") -> ExpiryEntry:
        if not key:
            raise ExpireError("Key must not be empty.")
        # Validate ISO format
        try:
            datetime.fromisoformat(expires_at)
        except ValueError as exc:
            raise ExpireError(f"Invalid date format: {expires_at}") from exc
        entries = self._load()
        entry = ExpiryEntry(key=key, expires_at=expires_at, note=note)
        entries[key] = entry
        self._save(entries)
        return entry

    def remove(self, key: str) -> None:
        entries = self._load()
        if key not in entries:
            raise ExpireError(f"No expiry set for key: {key}")
        del entries[key]
        self._save(entries)

    def list_entries(self) -> List[ExpiryEntry]:
        return list(self._load().values())

    def check(self) -> List[ExpiryEntry]:
        """Return all entries that are currently expired."""
        return [e for e in self._load().values() if e.is_expired()]
