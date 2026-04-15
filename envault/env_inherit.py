"""Env inheritance: merge a base env file into a child, with override semantics."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class InheritError(Exception):
    """Raised when inheritance operations fail."""


@dataclass
class InheritResult:
    base_path: Path
    child_path: Path
    added: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.added)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} key(s) inherited")
        if self.skipped:
            parts.append(f"{len(self.skipped)} key(s) skipped (already defined)")
        return ", ".join(parts) if parts else "nothing to inherit"


class InheritManager:
    def __init__(self, base_path: Path, child_path: Path) -> None:
        self.base_path = Path(base_path)
        self.child_path = Path(child_path)

    def _parse_env_file(self, path: Path) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            pairs[key.strip()] = value.strip()
        return pairs

    def _append_lines(self, path: Path, lines: List[str]) -> None:
        existing = path.read_text()
        separator = "" if existing.endswith("\n") or not existing else "\n"
        path.write_text(existing + separator + "\n".join(lines) + "\n")

    def apply(
        self,
        overwrite: bool = False,
        prefix: Optional[str] = None,
    ) -> InheritResult:
        if not self.base_path.exists():
            raise InheritError(f"Base file not found: {self.base_path}")
        if not self.child_path.exists():
            raise InheritError(f"Child file not found: {self.child_path}")

        base_pairs = self._parse_env_file(self.base_path)
        child_pairs = self._parse_env_file(self.child_path)

        result = InheritResult(base_path=self.base_path, child_path=self.child_path)
        new_lines: List[str] = []

        for key, value in base_pairs.items():
            dest_key = f"{prefix}{key}" if prefix else key
            if dest_key in child_pairs and not overwrite:
                result.skipped.append(dest_key)
            else:
                new_lines.append(f"{dest_key}={value}")
                result.added.append(dest_key)

        if new_lines:
            self._append_lines(self.child_path, new_lines)

        return result
