"""Truncate long env variable values for display purposes."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class TruncateError(Exception):
    pass


@dataclass
class TruncateResult:
    pairs: Dict[str, str] = field(default_factory=dict)
    truncated_keys: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.truncated_keys)

    def summary(self) -> str:
        if not self.truncated_keys:
            return "No values truncated."
        keys = ", ".join(self.truncated_keys)
        return f"Truncated {len(self.truncated_keys)} value(s): {keys}"

    def as_text(self) -> str:
        lines = []
        for k, v in self.pairs.items():
            marker = "*" if k in self.truncated_keys else " "
            lines.append(f"{marker} {k}={v}")
        return "\n".join(lines)


class TruncateManager:
    def __init__(self, max_length: int = 40) -> None:
        if max_length < 4:
            raise TruncateError("max_length must be at least 4")
        self.max_length = max_length

    def _parse_lines(self, text: str) -> List[tuple]:
        pairs = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            pairs.append((key.strip(), value.strip()))
        return pairs

    def truncate(self, env_file: Path, max_length: Optional[int] = None) -> TruncateResult:
        if not env_file.exists():
            raise TruncateError(f"File not found: {env_file}")
        limit = max_length if max_length is not None else self.max_length
        if limit < 4:
            raise TruncateError("max_length must be at least 4")
        text = env_file.read_text(encoding="utf-8")
        pairs = self._parse_lines(text)
        result = TruncateResult()
        for key, value in pairs:
            if len(value) > limit:
                result.pairs[key] = value[: limit - 3] + "..."
                result.truncated_keys.append(key)
            else:
                result.pairs[key] = value
        return result
