"""Mask sensitive values in .env files for safe display."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class MaskError(Exception):
    """Raised when masking operations fail."""


@dataclass
class MaskResult:
    original_keys: List[str] = field(default_factory=list)
    masked_keys: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)

    def as_text(self) -> str:
        return "\n".join(self.lines)


_SENSITIVE_RE = re.compile(
    r"(password|secret|token|key|api|auth|private|credential|pwd)",
    re.IGNORECASE,
)


class MaskManager:
    def __init__(self, show_chars: int = 4, mask_char: str = "*") -> None:
        self.show_chars = show_chars
        self.mask_char = mask_char

    def _is_sensitive(self, key: str) -> bool:
        return bool(_SENSITIVE_RE.search(key))

    def _mask_value(self, value: str) -> str:
        if len(value) <= self.show_chars:
            return self.mask_char * len(value)
        visible = value[: self.show_chars]
        return visible + self.mask_char * (len(value) - self.show_chars)

    def mask_file(
        self,
        env_file: Path,
        keys: Optional[List[str]] = None,
        auto_detect: bool = True,
    ) -> MaskResult:
        if not env_file.exists():
            raise MaskError(f"File not found: {env_file}")

        raw = env_file.read_text(encoding="utf-8")
        return self.mask_text(raw, keys=keys, auto_detect=auto_detect)

    def mask_text(
        self,
        text: str,
        keys: Optional[List[str]] = None,
        auto_detect: bool = True,
    ) -> MaskResult:
        explicit: set = set(keys) if keys else set()
        result = MaskResult()

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                result.lines.append(line)
                continue

            if "=" not in stripped:
                result.lines.append(line)
                continue

            k, _, v = stripped.partition("=")
            k = k.strip()
            v = v.strip()
            result.original_keys.append(k)

            should_mask = k in explicit or (auto_detect and self._is_sensitive(k))
            if should_mask:
                result.masked_keys.append(k)
                result.lines.append(f"{k}={self._mask_value(v)}")
            else:
                result.lines.append(line)

        return result

    def mask_dict(self, data: Dict[str, str], keys: Optional[List[str]] = None, auto_detect: bool = True) -> Dict[str, str]:
        explicit: set = set(keys) if keys else set()
        out: Dict[str, str] = {}
        for k, v in data.items():
            if k in explicit or (auto_detect and self._is_sensitive(k)):
                out[k] = self._mask_value(v)
            else:
                out[k] = v
        return out
