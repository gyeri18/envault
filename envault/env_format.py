"""Formatting and normalization utilities for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class FormatError(Exception):
    """Raised when formatting fails."""


@dataclass
class FormatResult:
    path: Path
    original_lines: int
    formatted_lines: int
    changes: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.changes)


class FormatManager:
    """Normalises .env file style: quote style, spacing, blank lines."""

    def __init__(
        self,
        quote_values: bool = False,
        strip_trailing_whitespace: bool = True,
        collapse_blank_lines: bool = True,
    ) -> None:
        self.quote_values = quote_values
        self.strip_trailing_whitespace = strip_trailing_whitespace
        self.collapse_blank_lines = collapse_blank_lines

    # ------------------------------------------------------------------
    def format(self, env_path: Path, *, dry_run: bool = False) -> FormatResult:
        if not env_path.exists():
            raise FormatError(f"File not found: {env_path}")

        original = env_path.read_text(encoding="utf-8")
        lines = original.splitlines()
        original_count = len(lines)
        changes: List[str] = []

        processed: List[str] = []
        prev_blank = False

        for raw in lines:
            line = raw.rstrip() if self.strip_trailing_whitespace else raw

            # Track trailing-whitespace changes
            if line != raw:
                changes.append(f"stripped trailing whitespace")

            # Collapse consecutive blank lines
            if line == "":
                if self.collapse_blank_lines and prev_blank:
                    changes.append("removed consecutive blank line")
                    continue
                prev_blank = True
                processed.append(line)
                continue

            prev_blank = False

            # Skip comments
            if line.lstrip().startswith("#"):
                processed.append(line)
                continue

            # Normalise KEY=VALUE spacing and optional quoting
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                if self.quote_values and value and not (
                    (value.startswith('"') and value.endswith('"'))
                    or (value.startswith("'") and value.endswith("'"))
                ):
                    value = f'"{value}"'
                    changes.append(f"quoted value for {key}")

                new_line = f"{key}={value}"
                if new_line != line:
                    changes.append(f"normalised spacing for {key}")
                line = new_line

            processed.append(line)

        formatted = "\n".join(processed) + "\n"

        if not dry_run and formatted != original:
            env_path.write_text(formatted, encoding="utf-8")

        return FormatResult(
            path=env_path,
            original_lines=original_count,
            formatted_lines=len(processed),
            changes=list(dict.fromkeys(changes)),  # deduplicate, preserve order
        )
