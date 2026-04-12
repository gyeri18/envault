"""Auto-fix common lint issues in .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.exceptions import EnvaultError


class LintFixError(EnvaultError):
    """Raised when a lint-fix operation fails."""


@dataclass
class LintFixResult:
    fixes_applied: List[str] = field(default_factory=list)
    original_lines: int = 0
    fixed_lines: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.fixes_applied)

    def summary(self) -> str:
        if not self.changed:
            return "No fixes needed."
        return f"{len(self.fixes_applied)} fix(es) applied: " + ", ".join(self.fixes_applied)


class LintFixManager:
    def __init__(self, env_path: Path) -> None:
        self.env_path = Path(env_path)

    def fix(self, *, remove_duplicates: bool = True, strip_whitespace: bool = True,
            remove_blank_runs: bool = True) -> LintFixResult:
        if not self.env_path.exists():
            raise LintFixError(f"File not found: {self.env_path}")

        raw = self.env_path.read_text(encoding="utf-8")
        lines = raw.splitlines()
        result = LintFixResult(original_lines=len(lines))
        out: List[str] = []

        seen_keys: set = set()
        prev_blank = False

        for line in lines:
            stripped = line.strip()

            # Strip inline whitespace around '='
            if strip_whitespace and "=" in stripped and not stripped.startswith("#"):
                key, _, val = stripped.partition("=")
                clean = f"{key.strip()}={val.strip()}"
                if clean != stripped:
                    result.fixes_applied.append(f"stripped whitespace on '{key.strip()}'")
                stripped = clean
                line = clean
            else:
                if strip_whitespace and line != stripped and not stripped.startswith("#") and stripped:
                    result.fixes_applied.append("stripped trailing whitespace")
                    line = stripped

            # Remove duplicate keys
            if remove_duplicates and "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0].strip()
                if key in seen_keys:
                    result.fixes_applied.append(f"removed duplicate key '{key}'")
                    continue
                seen_keys.add(key)

            # Collapse multiple blank lines
            if remove_blank_runs:
                if stripped == "":
                    if prev_blank:
                        result.fixes_applied.append("collapsed blank lines")
                        continue
                    prev_blank = True
                else:
                    prev_blank = False

            out.append(line)

        fixed_content = "\n".join(out)
        if not fixed_content.endswith("\n") and out:
            fixed_content += "\n"

        result.fixed_lines = len(out)
        if result.changed:
            self.env_path.write_text(fixed_content, encoding="utf-8")
        return result
