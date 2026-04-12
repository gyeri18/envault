"""Summarise differences between two .env files in human-readable form."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SummaryLine:
    status: str   # 'added', 'removed', 'changed', 'unchanged'
    key: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "added":
            return f"[+] {self.key}={self.new_value}"
        if self.status == "removed":
            return f"[-] {self.key}={self.old_value}"
        if self.status == "changed":
            return f"[~] {self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"[ ] {self.key}={self.new_value}"


@dataclass
class DiffSummary:
    lines: List[SummaryLine] = field(default_factory=list)

    @property
    def added(self) -> List[SummaryLine]:
        return [l for l in self.lines if l.status == "added"]

    @property
    def removed(self) -> List[SummaryLine]:
        return [l for l in self.lines if l.status == "removed"]

    @property
    def changed(self) -> List[SummaryLine]:
        return [l for l in self.lines if l.status == "changed"]

    @property
    def unchanged(self) -> List[SummaryLine]:
        return [l for l in self.lines if l.status == "unchanged"]

    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def render(self, show_unchanged: bool = False) -> str:
        parts: List[str] = []
        for line in self.lines:
            if line.status == "unchanged" and not show_unchanged:
                continue
            parts.append(str(line))
        return "\n".join(parts)


class DiffSummaryManager:
    def __init__(self, redact: bool = True) -> None:
        self._redact = redact

    def _parse(self, path: Path) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                pairs[key.strip()] = val.strip()
        return pairs

    def _maybe_redact(self, value: str) -> str:
        return "***" if self._redact else value

    def summarise(self, base: Path, target: Path) -> DiffSummary:
        base_pairs = self._parse(base)
        target_pairs = self._parse(target)
        all_keys = sorted(set(base_pairs) | set(target_pairs))
        summary = DiffSummary()
        for key in all_keys:
            in_base = key in base_pairs
            in_target = key in target_pairs
            if in_base and not in_target:
                summary.lines.append(SummaryLine("removed", key, old_value=self._maybe_redact(base_pairs[key])))
            elif in_target and not in_base:
                summary.lines.append(SummaryLine("added", key, new_value=self._maybe_redact(target_pairs[key])))
            elif base_pairs[key] != target_pairs[key]:
                summary.lines.append(SummaryLine("changed", key,
                                                  old_value=self._maybe_redact(base_pairs[key]),
                                                  new_value=self._maybe_redact(target_pairs[key])))
            else:
                summary.lines.append(SummaryLine("unchanged", key, new_value=self._maybe_redact(target_pairs[key])))
        return summary
