"""Filter .env file entries by prefix, suffix, or pattern."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Dict, List, Optional

from envault.exceptions import EnvaultError


class FilterManager:
    """Filter key-value pairs from a .env file."""

    def __init__(self, env_path: Path) -> None:
        self.env_path = Path(env_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(
        self,
        *,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        pattern: Optional[str] = None,
        invert: bool = False,
    ) -> Dict[str, str]:
        """Return key-value pairs that match the given criteria.

        Only one of *prefix*, *suffix*, or *pattern* (glob) may be supplied.
        Set *invert=True* to return non-matching pairs instead.

        Raises:
            EnvaultError: if the file does not exist or arguments are invalid.
        """
        if not self.env_path.exists():
            raise EnvaultError(f"File not found: {self.env_path}")

        criteria = sum(x is not None for x in (prefix, suffix, pattern))
        if criteria == 0:
            raise EnvaultError("Provide at least one of: prefix, suffix, pattern.")
        if criteria > 1:
            raise EnvaultError("Only one filter criterion may be used at a time.")

        pairs = self._parse_env_file()

        def matches(key: str) -> bool:
            if prefix is not None:
                return key.startswith(prefix)
            if suffix is not None:
                return key.endswith(suffix)
            # pattern
            return fnmatch.fnmatch(key, pattern)  # type: ignore[arg-type]

        return {
            k: v
            for k, v in pairs.items()
            if matches(k) != invert
        }

    def list_keys(
        self,
        *,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        pattern: Optional[str] = None,
        invert: bool = False,
    ) -> List[str]:
        """Convenience wrapper — return only the matching key names."""
        return list(
            self.filter(
                prefix=prefix,
                suffix=suffix,
                pattern=pattern,
                invert=invert,
            ).keys()
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_env_file(self) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for raw in self.env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip().strip('"').strip("'")
        return pairs
