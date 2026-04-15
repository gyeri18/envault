"""Type-checking for .env file values against expected types."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


SUPPORTED_TYPES = {"str", "int", "float", "bool", "url", "email"}

_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}
_URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class TypeCheckError(Exception):
    """Raised for configuration errors in TypeCheckManager."""


@dataclass
class TypeViolation:
    key: str
    expected: str
    actual_value: str

    def __str__(self) -> str:
        return f"{self.key}: expected {self.expected}, got {self.actual_value!r}"


@dataclass
class TypeCheckResult:
    violations: List[TypeViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.ok:
            return "All values match expected types."
        lines = [f"{len(self.violations)} type violation(s):"]
        lines.extend(f"  - {v}" for v in self.violations)
        return "\n".join(lines)


class TypeCheckManager:
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"

    def _parse_env_file(self, path: Path) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip().strip('"').strip("'")
        return pairs

    def _check_value(self, value: str, expected_type: str) -> bool:
        if expected_type == "str":
            return True
        if expected_type == "int":
            try:
                int(value)
                return True
            except ValueError:
                return False
        if expected_type == "float":
            try:
                float(value)
                return True
            except ValueError:
                return False
        if expected_type == "bool":
            return value.lower() in _BOOL_TRUE | _BOOL_FALSE
        if expected_type == "url":
            return bool(_URL_RE.match(value))
        if expected_type == "email":
            return bool(_EMAIL_RE.match(value))
        raise TypeCheckError(f"Unsupported type: {expected_type!r}")

    def check(self, env_file: Path, schema: Dict[str, str]) -> TypeCheckResult:
        """Check values in *env_file* against *schema* (key -> expected type)."""
        for t in schema.values():
            if t not in SUPPORTED_TYPES:
                raise TypeCheckError(f"Unsupported type {t!r} in schema")
        if not env_file.exists():
            raise TypeCheckError(f"File not found: {env_file}")
        pairs = self._parse_env_file(env_file)
        violations: List[TypeViolation] = []
        for key, expected in schema.items():
            if key not in pairs:
                continue
            if not self._check_value(pairs[key], expected):
                violations.append(TypeViolation(key=key, expected=expected, actual_value=pairs[key]))
        return TypeCheckResult(violations=violations)
