"""Audit log for tracking vault operations per project."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class AuditLog:
    """Records and retrieves audit events for envault operations."""

    LOG_FILENAME = "audit.log"

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.envault"))
        self.log_path = self.config_dir / self.LOG_FILENAME
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def record(self, project: str, action: str, detail: str = "") -> None:
        """Append a single audit event to the log file."""
        entry = {
            "timestamp": self._now_iso(),
            "project": project,
            "action": action,
            "detail": detail,
        }
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    def get_entries(
        self, project: Optional[str] = None, limit: int = 50
    ) -> List[dict]:
        """Return recent audit entries, optionally filtered by project."""
        if not self.log_path.exists():
            return []

        entries = []
        with open(self.log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if project is None or entry.get("project") == project:
                    entries.append(entry)

        return entries[-limit:]

    def clear(self, project: Optional[str] = None) -> int:
        """Remove entries for a project (or all). Returns number removed."""
        if not self.log_path.exists():
            return 0

        kept, removed = [], 0
        with open(self.log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    kept.append(line)
                    continue
                if project is not None and entry.get("project") != project:
                    kept.append(json.dumps(entry))
                else:
                    removed += 1

        with open(self.log_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(kept) + ("\n" if kept else ""))

        return removed
