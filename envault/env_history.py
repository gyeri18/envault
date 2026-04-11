"""Track change history for .env keys across lock/unlock operations."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class HistoryEntry:
    timestamp: str
    project: str
    key: str
    action: str          # 'set', 'delete', 'rotate'
    old_value_hash: Optional[str]
    new_value_hash: Optional[str]

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.action.upper()} {self.key} (project={self.project})"


class HistoryManager:
    """Records and retrieves per-key change history for a project."""

    def __init__(self, config_dir: Path, project: str) -> None:
        self._config_dir = Path(config_dir)
        self._project = project
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        history_dir = self._config_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)

    def _history_path(self) -> Path:
        return self._config_dir / "history" / f"{self._project}.jsonl"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _hash_value(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()[:12]

    def record(self, key: str, action: str,
               old_value: Optional[str] = None,
               new_value: Optional[str] = None) -> HistoryEntry:
        if action not in ("set", "delete", "rotate"):
            raise ValueError(f"Unknown action: {action!r}")
        entry = HistoryEntry(
            timestamp=self._now_iso(),
            project=self._project,
            key=key,
            action=action,
            old_value_hash=self._hash_value(old_value),
            new_value_hash=self._hash_value(new_value),
        )
        with self._history_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry)) + "\n")
        return entry

    def get_entries(self, key: Optional[str] = None) -> List[HistoryEntry]:
        path = self._history_path()
        if not path.exists():
            return []
        entries: List[HistoryEntry] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entry = HistoryEntry(**data)
            if key is None or entry.key == key:
                entries.append(entry)
        return entries

    def clear(self) -> None:
        path = self._history_path()
        if path.exists():
            path.unlink()
