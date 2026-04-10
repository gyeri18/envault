"""Transform .env variable values using built-in or custom operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from envault.exceptions import EnvaultError


class TransformError(EnvaultError):
    """Raised when a transformation fails."""


# Built-in transform functions
_TRANSFORMS: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "quote": lambda v: f'"{v}"',
    "unquote": lambda v: v.strip('"\"'),
    "base64encode": lambda v: __import__("base64").b64encode(v.encode()).decode(),
    "base64decode": lambda v: __import__("base64").b64decode(v.encode()).decode(),
}


class TransformManager:
    def __init__(self, env_path: Path) -> None:
        self.env_path = Path(env_path)

    def _parse_lines(self) -> List[Tuple[str, str, str]]:
        """Return list of (key, value, raw_line) tuples, preserving comments/blanks."""
        results: List[Tuple[str, str, str]] = []
        for raw in self.env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                results.append(("", "", raw))
                continue
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
            if match:
                results.append((match.group(1), match.group(2), raw))
            else:
                results.append(("", "", raw))
        return results

    def _write_lines(self, lines: List[Tuple[str, str, str]]) -> None:
        output = []
        for key, value, raw in lines:
            if key:
                output.append(f"{key}={value}")
            else:
                output.append(raw)
        self.env_path.write_text("\n".join(output) + "\n")

    def available_transforms(self) -> List[str]:
        return list(_TRANSFORMS.keys())

    def transform(
        self,
        operation: str,
        keys: Optional[List[str]] = None,
        pattern: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Tuple[str, str]]:
        """Apply *operation* to matching keys. Returns {key: (old, new)}."""
        if operation not in _TRANSFORMS:
            raise TransformError(
                f"Unknown transform '{operation}'. "
                f"Available: {', '.join(_TRANSFORMS)}"
            )
        fn = _TRANSFORMS[operation]
        lines = self._parse_lines()
        changed: Dict[str, Tuple[str, str]] = {}

        updated = []
        for key, value, raw in lines:
            if not key:
                updated.append((key, value, raw))
                continue
            should_apply = (
                (keys and key in keys)
                or (pattern and re.search(pattern, key))
                or (not keys and not pattern)
            )
            if should_apply:
                new_value = fn(value)
                if new_value != value:
                    changed[key] = (value, new_value)
                updated.append((key, new_value, raw))
            else:
                updated.append((key, value, raw))

        if not dry_run:
            self._write_lines(updated)
        return changed
