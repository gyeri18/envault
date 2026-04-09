"""Lint .env files for common issues and best practices."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.exceptions import EnvaultError


@dataclass
class LintIssue:
    line: int
    key: str
    severity: str  # 'error' | 'warning' | 'info'
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line} ({self.key}): {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)


class LintManager:
    _VALID_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
    _LINE_RE = re.compile(r"^\s*([^#=\s][^=]*)=(.*)$")

    def __init__(self) -> None:
        pass

    def lint(self, env_path: Path) -> LintResult:
        if not env_path.exists():
            raise EnvaultError(f"File not found: {env_path}")

        result = LintResult(path=str(env_path))
        seen_keys: dict[str, int] = {}

        for lineno, raw in enumerate(env_path.read_text().splitlines(), start=1):
            stripped = raw.strip()

            if not stripped or stripped.startswith("#"):
                continue

            m = self._LINE_RE.match(raw)
            if not m:
                result.issues.append(
                    LintIssue(lineno, "<unknown>", "error", "Invalid line format (expected KEY=VALUE)")
                )
                continue

            key, value = m.group(1).strip(), m.group(2)

            if not self._VALID_KEY_RE.match(key):
                result.issues.append(
                    LintIssue(lineno, key, "warning", "Key should be UPPER_SNAKE_CASE")
                )

            if key in seen_keys:
                result.issues.append(
                    LintIssue(lineno, key, "error", f"Duplicate key (first seen on line {seen_keys[key]})")
                )
            else:
                seen_keys[key] = lineno

            if not value:
                result.issues.append(
                    LintIssue(lineno, key, "info", "Empty value")
                )

            if any(p in key for p in ("SECRET", "PASSWORD", "TOKEN", "KEY")) and value and not value.startswith('"'):
                result.issues.append(
                    LintIssue(lineno, key, "warning", "Sensitive value should be quoted")
                )

        return result
