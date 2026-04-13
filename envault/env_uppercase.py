"""Enforce or check that all .env keys are uppercase."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


class UppercaseError(Exception):
    """Raised when an uppercase operation fails."""


@dataclass
class UppercaseResult:
    converted: List[Tuple[str, str]] = field(default_factory=list)  # (original, new)
    skipped: List[str] = field(default_factory=list)  # already uppercase

    @property
    def changed(self) -> bool:
        return bool(self.converted)

    @property
    def summary(self) -> str:
        if not self.changed:
            return "All keys are already uppercase."
        lines = [f"Converted {len(self.converted)} key(s) to uppercase:"]
        for orig, new in self.converted:
            lines.append(f"  {orig} -> {new}")
        return "\n".join(lines)


class UppercaseManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir  # reserved for future audit integration

    # ------------------------------------------------------------------
    def _parse_lines(self, text: str) -> List[str]:
        return text.splitlines(keepends=True)

    def check(self, env_file: Path) -> List[str]:
        """Return a list of keys that are not fully uppercase."""
        if not env_file.exists():
            raise UppercaseError(f"File not found: {env_file}")
        offenders: List[str] = []
        for line in env_file.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key != key.upper():
                    offenders.append(key)
        return offenders

    def fix(self, env_file: Path, dry_run: bool = False) -> UppercaseResult:
        """Convert all keys to uppercase in-place (unless *dry_run*)."""
        if not env_file.exists():
            raise UppercaseError(f"File not found: {env_file}")

        result = UppercaseResult()
        raw_lines = self._parse_lines(env_file.read_text())
        output_lines: List[str] = []

        for line in raw_lines:
            stripped = line.rstrip("\n").rstrip("\r")
            s = stripped.strip()
            if s and not s.startswith("#") and "=" in s:
                key, rest = stripped.split("=", 1)
                upper_key = key.strip().upper()
                if key.strip() != upper_key:
                    result.converted.append((key.strip(), upper_key))
                    line = line.replace(key, upper_key, 1)
                else:
                    result.skipped.append(key.strip())
            output_lines.append(line)

        if result.changed and not dry_run:
            env_file.write_text("".join(output_lines))

        return result
