"""Redaction manager for masking sensitive values in .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.exceptions import EnvaultError


DEFAULT_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)",
]


@dataclass
class RedactResult:
    original_path: Path
    redacted_lines: List[str]
    redacted_keys: List[str] = field(default_factory=list)

    def write(self, dest: Path) -> None:
        dest.write_text("\n".join(self.redacted_lines) + "\n", encoding="utf-8")


class RedactManager:
    """Mask sensitive values in a .env file based on key-name patterns."""

    MASK = "***REDACTED***"

    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        mask: str = MASK,
    ) -> None:
        raw = patterns if patterns is not None else DEFAULT_PATTERNS
        try:
            self._regexes = [re.compile(p) for p in raw]
        except re.error as exc:
            raise EnvaultError(f"Invalid redaction pattern: {exc}") from exc
        self.mask = mask

    # ------------------------------------------------------------------
    def _is_sensitive(self, key: str) -> bool:
        return any(rx.search(key) for rx in self._regexes)

    def _parse_line(self, line: str) -> Optional[tuple[str, str, str]]:
        """Return (key, sep, value) or None if not a key=value line."""
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return None
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*)", stripped)
        if not match:
            return None
        return match.group(1), match.group(2), match.group(3)

    # ------------------------------------------------------------------
    def redact(self, env_file: Path, dest: Optional[Path] = None) -> RedactResult:
        """Redact *env_file* and optionally write result to *dest*."""
        if not env_file.exists():
            raise EnvaultError(f"File not found: {env_file}")

        lines = env_file.read_text(encoding="utf-8").splitlines()
        output: List[str] = []
        redacted_keys: List[str] = []

        for line in lines:
            parsed = self._parse_line(line)
            if parsed and self._is_sensitive(parsed[0]):
                key, sep, _ = parsed
                output.append(f"{key}{sep}{self.mask}")
                redacted_keys.append(key)
            else:
                output.append(line)

        result = RedactResult(
            original_path=env_file,
            redacted_lines=output,
            redacted_keys=redacted_keys,
        )
        if dest is not None:
            result.write(dest)
        return result

    def sensitive_keys(self, env_file: Path) -> Dict[str, str]:
        """Return a dict of {key: original_value} for all sensitive keys."""
        if not env_file.exists():
            raise EnvaultError(f"File not found: {env_file}")
        pairs: Dict[str, str] = {}
        for line in env_file.read_text(encoding="utf-8").splitlines():
            parsed = self._parse_line(line)
            if parsed and self._is_sensitive(parsed[0]):
                pairs[parsed[0]] = parsed[2]
        return pairs
