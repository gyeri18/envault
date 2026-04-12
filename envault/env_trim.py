"""Trim whitespace from .env variable values."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


class TrimError(Exception):
    """Raised when trimming fails."""


@dataclass
class TrimResult:
    trimmed: List[str] = field(default_factory=list)  # keys whose values changed
    total: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.trimmed)

    def summary(self) -> str:
        if not self.changed:
            return f"No values needed trimming ({self.total} keys checked)."
        keys = ", ".join(self.trimmed)
        return (
            f"Trimmed {len(self.trimmed)} of {self.total} values: {keys}."
        )


class TrimManager:
    def __init__(self, env_path: Path) -> None:
        self.env_path = Path(env_path)

    def _parse_lines(
        self, lines: List[str]
    ) -> List[Tuple[str, str | None]]:  # (raw_line, key_or_None)
        parsed: List[Tuple[str, str | None]] = []
        for line in lines:
            stripped = line.rstrip("\n")
            if stripped.lstrip().startswith("#") or "=" not in stripped:
                parsed.append((stripped, None))
            else:
                parsed.append((stripped, stripped.split("=", 1)[0].strip()))
        return parsed

    def trim(self, *, dry_run: bool = False) -> TrimResult:
        """Strip leading/trailing whitespace from all values in the env file.

        Parameters
        ----------
        dry_run:
            When *True* the file is not modified; only the result is returned.
        """
        if not self.env_path.exists():
            raise TrimError(f"File not found: {self.env_path}")

        raw_lines = self.env_path.read_text(encoding="utf-8").splitlines()
        result = TrimResult()
        new_lines: List[str] = []

        for line in raw_lines:
            stripped = line.rstrip("\n")
            if stripped.lstrip().startswith("#") or "=" not in stripped:
                new_lines.append(stripped)
                continue

            key, _, value = stripped.partition("=")
            key_clean = key.strip()
            value_trimmed = value.strip()
            result.total += 1

            if value != value_trimmed:
                result.trimmed.append(key_clean)
                new_lines.append(f"{key_clean}={value_trimmed}")
            else:
                new_lines.append(stripped)

        if result.changed and not dry_run:
            self.env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        return result
