"""Variable interpolation for .env files.

Expands ${VAR} and $VAR references within values using other keys
in the same file or an optional external context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


class InterpolateError(Exception):
    """Raised when interpolation fails."""


@dataclass
class InterpolateResult:
    pairs: Dict[str, str] = field(default_factory=dict)
    unresolved: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.unresolved) == 0

    def summary(self) -> str:
        if self.ok:
            return f"Interpolated {len(self.pairs)} key(s) with no unresolved references."
        return (
            f"Interpolated {len(self.pairs)} key(s); "
            f"{len(self.unresolved)} unresolved reference(s): {', '.join(self.unresolved)}"
        )


class InterpolateManager:
    def __init__(self, env_file: Path, config_dir: Optional[Path] = None) -> None:
        self.env_file = Path(env_file)

    def _parse_lines(self, text: str) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            pairs[key.strip()] = value.strip().strip('"').strip("'")
        return pairs

    def interpolate(
        self, context: Optional[Dict[str, str]] = None
    ) -> InterpolateResult:
        """Expand variable references in values; return resolved pairs."""
        if not self.env_file.exists():
            raise InterpolateError(f"File not found: {self.env_file}")

        raw = self._parse_lines(self.env_file.read_text())
        merged = dict(context or {})
        merged.update(raw)  # file values take precedence for self-refs

        resolved: Dict[str, str] = {}
        unresolved_refs: List[str] = []

        for key, value in raw.items():
            expanded, missing = self._expand(value, merged)
            resolved[key] = expanded
            unresolved_refs.extend(missing)

        return InterpolateResult(pairs=resolved, unresolved=list(dict.fromkeys(unresolved_refs)))

    def _expand(self, value: str, context: Dict[str, str]):
        missing: List[str] = []

        def replacer(m: re.Match) -> str:
            ref = m.group(1) or m.group(2)
            if ref in context:
                return context[ref]
            missing.append(ref)
            return m.group(0)

        expanded = _REF_RE.sub(replacer, value)
        return expanded, missing
