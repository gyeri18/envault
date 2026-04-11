"""Manage inline comments on .env file keys."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class CommentError(Exception):
    """Raised when a comment operation fails."""


@dataclass
class CommentEntry:
    key: str
    comment: str

    def __str__(self) -> str:
        return f"{self.key}: {self.comment}"


class CommentManager:
    """Add, remove, and list inline comments on .env keys."""

    _PAIR_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")
    _COMMENT_RE = re.compile(r"^(.+?)\s*#\s*(.+)$")

    def __init__(self, env_path: Path) -> None:
        self.env_path = Path(env_path)

    # ------------------------------------------------------------------
    def _read_lines(self) -> List[str]:
        if not self.env_path.exists():
            raise CommentError(f"File not found: {self.env_path}")
        return self.env_path.read_text().splitlines(keepends=True)

    def _write_lines(self, lines: List[str]) -> None:
        self.env_path.write_text("".join(lines))

    # ------------------------------------------------------------------
    def set(self, key: str, comment: str) -> None:
        """Add or replace the inline comment for *key*."""
        if not key:
            raise CommentError("Key must not be empty.")
        if not comment:
            raise CommentError("Comment must not be empty.")
        lines = self._read_lines()
        found = False
        for i, line in enumerate(lines):
            m = self._PAIR_RE.match(line.rstrip("\n"))
            if m and m.group(1) == key:
                raw_value = m.group(2)
                # Strip existing comment from value
                vc = self._COMMENT_RE.match(raw_value)
                bare_value = vc.group(1) if vc else raw_value
                lines[i] = f"{key}={bare_value}  # {comment}\n"
                found = True
                break
        if not found:
            raise CommentError(f"Key '{key}' not found in {self.env_path}")
        self._write_lines(lines)

    def remove(self, key: str) -> None:
        """Remove the inline comment from *key* (no-op if none exists)."""
        if not key:
            raise CommentError("Key must not be empty.")
        lines = self._read_lines()
        found = False
        for i, line in enumerate(lines):
            m = self._PAIR_RE.match(line.rstrip("\n"))
            if m and m.group(1) == key:
                raw_value = m.group(2)
                vc = self._COMMENT_RE.match(raw_value)
                bare_value = vc.group(1) if vc else raw_value
                lines[i] = f"{key}={bare_value}\n"
                found = True
                break
        if not found:
            raise CommentError(f"Key '{key}' not found in {self.env_path}")
        self._write_lines(lines)

    def list(self) -> List[CommentEntry]:
        """Return all keys that have an inline comment."""
        entries: List[CommentEntry] = []
        for line in self._read_lines():
            m = self._PAIR_RE.match(line.rstrip("\n"))
            if not m:
                continue
            vc = self._COMMENT_RE.match(m.group(2))
            if vc:
                entries.append(CommentEntry(key=m.group(1), comment=vc.group(2)))
        return entries
