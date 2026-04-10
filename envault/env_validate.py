"""Validation of .env files against a schema definition."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.exceptions import EnvaultError


SCHEMA_LINE_RE = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)'
    r'(?P<required>!?)'
    r'(?::(?P<type>str|int|bool|url|email))?'
    r'(?:\s*#.*)?$'
)


@dataclass
class ValidationIssue:
    key: str
    message: str
    level: str = "error"  # 'error' or 'warning'

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]


class ValidateManager:
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"

    # ------------------------------------------------------------------
    def load_schema(self, schema_path: Path) -> Dict[str, dict]:
        """Parse a .envschema file into a dict of key -> {required, type}."""
        schema: Dict[str, dict] = {}
        for lineno, raw in enumerate(schema_path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = SCHEMA_LINE_RE.match(line)
            if not m:
                raise EnvaultError(f"Invalid schema syntax on line {lineno}: {raw!r}")
            schema[m.group("key")] = {
                "required": m.group("required") == "!",
                "type": m.group("type") or "str",
            }
        return schema

    # ------------------------------------------------------------------
    def validate(self, env_path: Path, schema_path: Path) -> ValidationResult:
        """Validate *env_path* against *schema_path*."""
        schema = self.load_schema(schema_path)
        env_vars = self._parse_env(env_path)
        result = ValidationResult()

        for key, meta in schema.items():
            if key not in env_vars:
                if meta["required"]:
                    result.issues.append(ValidationIssue(key, "required key is missing"))
                else:
                    result.issues.append(ValidationIssue(key, "optional key not set", "warning"))
                continue
            value = env_vars[key]
            type_error = self._check_type(value, meta["type"])
            if type_error:
                result.issues.append(ValidationIssue(key, type_error))

        return result

    # ------------------------------------------------------------------
    def _parse_env(self, path: Path) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            pairs[k.strip()] = v.strip().strip('"\'')
        return pairs

    def _check_type(self, value: str, expected: str) -> Optional[str]:
        if expected == "int":
            if not re.fullmatch(r'-?\d+', value):
                return f"expected int, got {value!r}"
        elif expected == "bool":
            if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
                return f"expected bool, got {value!r}"
        elif expected == "url":
            if not re.match(r'https?://', value):
                return f"expected url starting with http(s)://, got {value!r}"
        elif expected == "email":
            if not re.fullmatch(r'[^@]+@[^@]+\.[^@]+', value):
                return f"expected email address, got {value!r}"
        return None
