"""Export audit log entries to various formats (JSON, CSV, text)."""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from envault.audit import AuditLog
from envault.exceptions import EnvaultError


class AuditExportError(EnvaultError):
    """Raised when audit export fails."""


@dataclass
class AuditExportResult:
    format: str
    entry_count: int
    output: str

    def write(self, path: Path) -> None:
        path.write_text(self.output, encoding="utf-8")


class AuditExportManager:
    FORMATS = ("json", "csv", "text")

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self._audit = AuditLog(config_dir=config_dir)

    def export(
        self,
        fmt: str = "json",
        project: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AuditExportResult:
        if fmt not in self.FORMATS:
            raise AuditExportError(
                f"Unsupported format '{fmt}'. Choose from: {', '.join(self.FORMATS)}"
            )

        entries = self._audit.get_entries(project=project)
        if limit is not None:
            entries = entries[-limit:]

        if fmt == "json":
            output = json.dumps(entries, indent=2)
        elif fmt == "csv":
            output = self._to_csv(entries)
        else:
            output = self._to_text(entries)

        return AuditExportResult(format=fmt, entry_count=len(entries), output=output)

    def _to_csv(self, entries: List[dict]) -> str:
        if not entries:
            return ""
        buf = io.StringIO()
        fieldnames = list(entries[0].keys()) if entries else ["timestamp", "action", "project", "detail"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)
        return buf.getvalue()

    def _to_text(self, entries: List[dict]) -> str:
        lines = []
        for e in entries:
            ts = e.get("timestamp", "?")
            action = e.get("action", "?")
            project = e.get("project", "-")
            detail = e.get("detail", "")
            line = f"[{ts}] {action} | project={project}"
            if detail:
                line += f" | {detail}"
            lines.append(line)
        return "\n".join(lines)
