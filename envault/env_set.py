"""Set or update individual key-value pairs in a .env file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SetError(Exception):
    """Raised when a set operation fails."""


@dataclass
class SetResult:
    updated: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.updated or self.added)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"added: {', '.join(self.added)}")
        if self.updated:
            parts.append(f"updated: {', '.join(self.updated)}")
        return "; ".join(parts) if parts else "no changes"


class SetManager:
    def __init__(self, env_file: Path) -> None:
        self.env_file = Path(env_file)

    def _parse_lines(self) -> List[str]:
        if not self.env_file.exists():
            return []
        return self.env_file.read_text().splitlines(keepends=True)

    def set(self, pairs: Dict[str, str], create: bool = True) -> SetResult:
        """Set one or more key=value pairs in the env file.

        Args:
            pairs: Mapping of key -> value to set.
            create: If True, create the file when it does not exist.

        Returns:
            SetResult describing what was added/updated.

        Raises:
            SetError: If the file does not exist and *create* is False.
        """
        if not self.env_file.exists():
            if not create:
                raise SetError(f"File not found: {self.env_file}")
            self.env_file.parent.mkdir(parents=True, exist_ok=True)
            self.env_file.write_text("")

        lines = self._parse_lines()
        result = SetResult()
        remaining = dict(pairs)

        new_lines: List[str] = []
        for line in lines:
            stripped = line.rstrip("\n")
            if "=" in stripped and not stripped.lstrip().startswith("#"):
                key, _, _ = stripped.partition("=")
                key = key.strip()
                if key in remaining:
                    new_lines.append(f"{key}={remaining.pop(key)}\n")
                    result.updated.append(key)
                    continue
            new_lines.append(line if line.endswith("\n") else line + "\n" if line else line)

        for key, value in remaining.items():
            new_lines.append(f"{key}={value}\n")
            result.added.append(key)

        self.env_file.write_text("".join(new_lines))
        return result

    def unset(self, keys: List[str]) -> List[str]:
        """Remove keys from the env file. Returns list of actually removed keys."""
        if not self.env_file.exists():
            raise SetError(f"File not found: {self.env_file}")

        lines = self._parse_lines()
        removed: List[str] = []
        new_lines: List[str] = []
        for line in lines:
            stripped = line.rstrip("\n")
            if "=" in stripped and not stripped.lstrip().startswith("#"):
                key, _, _ = stripped.partition("=")
                if key.strip() in keys:
                    removed.append(key.strip())
                    continue
            new_lines.append(line)
        self.env_file.write_text("".join(new_lines))
        return removed
