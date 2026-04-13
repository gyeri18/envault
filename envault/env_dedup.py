"""Deduplication manager for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


class DedupError(Exception):
    """Raised when deduplication fails."""


@dataclass
class DedupResult:
    removed: List[Tuple[str, str]] = field(default_factory=list)  # (key, duplicate_value)
    kept: Dict[str, str] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return len(self.removed) > 0

    @property
    def summary(self) -> str:
        if not self.changed:
            return "No duplicate keys found."
        keys = ", ".join(sorted({k for k, _ in self.removed}))
        return f"Removed {len(self.removed)} duplicate(s) for key(s): {keys}"


class DedupManager:
    def __init__(self, config_dir: str | None = None) -> None:
        self._config_dir = config_dir  # reserved for future use

    def _parse_lines(self, text: str) -> List[str]:
        return text.splitlines(keepends=True)

    def deduplicate(self, env_file: str, keep: str = "last") -> DedupResult:
        """Remove duplicate keys from *env_file*.

        Args:
            env_file: Path to the .env file.
            keep: ``"last"`` (default) keeps the final occurrence;
                  ``"first"`` keeps the first occurrence.
        """
        path = Path(env_file)
        if not path.exists():
            raise DedupError(f"File not found: {env_file}")
        if keep not in ("first", "last"):
            raise DedupError(f"Invalid keep strategy: {keep!r}. Use 'first' or 'last'.")

        lines = self._parse_lines(path.read_text(encoding="utf-8"))
        result = DedupResult()

        # Collect (line_index, key, value) for assignment lines
        assignments: List[Tuple[int, str, str]] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            if key:
                assignments.append((idx, key, value.strip()))

        # Determine which indices to keep
        seen: Dict[str, int] = {}  # key -> line index to keep
        for idx, key, _ in assignments:
            if keep == "last":
                seen[key] = idx
            else:  # first
                seen.setdefault(key, idx)

        keep_indices = set(seen.values())
        new_lines: List[str] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            if not key:
                new_lines.append(line)
                continue
            if idx in keep_indices:
                new_lines.append(line)
                result.kept[key] = value.strip()
            else:
                result.removed.append((key, value.strip()))

        if result.changed:
            path.write_text("".join(new_lines), encoding="utf-8")

        return result
