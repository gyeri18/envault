"""Detect and resolve placeholder values in .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Matches values like <MY_VAR>, ${MY_VAR}, {{MY_VAR}}
_PLACEHOLDER_RE = re.compile(
    r'^(?:<([^>]+)>|\$\{([^}]+)\}|\{\{([^}]+)\}\})$'
)


class PlaceholderError(Exception):
    """Raised when placeholder resolution fails."""


@dataclass
class PlaceholderIssue:
    key: str
    placeholder: str
    line_number: int

    def __str__(self) -> str:
        return f"Line {self.line_number}: '{self.key}' has unresolved placeholder '{self.placeholder}'"


@dataclass
class PlaceholderResult:
    issues: List[PlaceholderIssue] = field(default_factory=list)
    resolved: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


class PlaceholderManager:
    def __init__(self, env_file: Path) -> None:
        self.env_file = Path(env_file)

    def _parse_lines(self) -> List[tuple]:
        """Return list of (line_number, key, value) for non-comment, non-blank lines."""
        pairs = []
        for i, line in enumerate(self.env_file.read_text().splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if '=' not in stripped:
                continue
            key, _, value = stripped.partition('=')
            pairs.append((i, key.strip(), value.strip()))
        return pairs

    def scan(self) -> PlaceholderResult:
        """Scan the env file and return all unresolved placeholder issues."""
        if not self.env_file.exists():
            raise PlaceholderError(f"File not found: {self.env_file}")
        result = PlaceholderResult()
        for lineno, key, value in self._parse_lines():
            m = _PLACEHOLDER_RE.match(value)
            if m:
                placeholder = next(g for g in m.groups() if g is not None)
                result.issues.append(PlaceholderIssue(key, placeholder, lineno))
        return result

    def resolve(self, overrides: Dict[str, str]) -> PlaceholderResult:
        """Resolve placeholders using the provided overrides dict.

        Returns a PlaceholderResult; any key still unresolved appears in issues.
        """
        if not self.env_file.exists():
            raise PlaceholderError(f"File not found: {self.env_file}")
        result = PlaceholderResult()
        lines = self.env_file.read_text().splitlines()
        new_lines: List[str] = []
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or '=' not in stripped:
                new_lines.append(line)
                continue
            key, _, value = stripped.partition('=')
            key = key.strip()
            value = value.strip()
            m = _PLACEHOLDER_RE.match(value)
            if m:
                placeholder = next(g for g in m.groups() if g is not None)
                if placeholder in overrides:
                    resolved_val = overrides[placeholder]
                    new_lines.append(f"{key}={resolved_val}")
                    result.resolved[key] = resolved_val
                else:
                    new_lines.append(line)
                    result.issues.append(PlaceholderIssue(key, placeholder, i))
            else:
                new_lines.append(line)
        self.env_file.write_text('\n'.join(new_lines) + '\n')
        return result
