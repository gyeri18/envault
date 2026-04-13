"""env_echo.py — Print resolved env vars to stdout with optional masking."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.exceptions import EnvaultError


class EchoError(EnvaultError):
    """Raised when the echo operation fails."""


@dataclass
class EchoResult:
    pairs: Dict[str, str] = field(default_factory=dict)
    masked_keys: List[str] = field(default_factory=list)

    def as_text(self, mask_char: str = "****") -> str:
        lines: List[str] = []
        for key, value in self.pairs.items():
            display = mask_char if key in self.masked_keys else value
            lines.append(f"{key}={display}")
        return "\n".join(lines)

    def as_export(self, mask_char: str = "****") -> str:
        lines: List[str] = []
        for key, value in self.pairs.items():
            display = mask_char if key in self.masked_keys else value
            lines.append(f"export {key}={display}")
        return "\n".join(lines)


_SENSITIVE_SUBSTRINGS = ("secret", "password", "passwd", "token", "api_key", "apikey", "private")


class EchoManager:
    def __init__(self, env_file: Path) -> None:
        self.env_file = Path(env_file)

    def _parse(self) -> Dict[str, str]:
        if not self.env_file.exists():
            raise EchoError(f"File not found: {self.env_file}")
        pairs: Dict[str, str] = {}
        for raw in self.env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip()
        return pairs

    def _auto_sensitive(self, keys: List[str]) -> List[str]:
        return [
            k for k in keys
            if any(s in k.lower() for s in _SENSITIVE_SUBSTRINGS)
        ]

    def echo(
        self,
        keys: Optional[List[str]] = None,
        mask: bool = False,
        mask_keys: Optional[List[str]] = None,
        auto_mask: bool = False,
    ) -> EchoResult:
        all_pairs = self._parse()

        if keys:
            missing = [k for k in keys if k not in all_pairs]
            if missing:
                raise EchoError(f"Keys not found: {', '.join(missing)}")
            selected = {k: all_pairs[k] for k in keys}
        else:
            selected = dict(all_pairs)

        masked: List[str] = []
        if mask:
            masked = list(selected.keys())
        else:
            if mask_keys:
                masked.extend(mask_keys)
            if auto_mask:
                masked.extend(self._auto_sensitive(list(selected.keys())))

        return EchoResult(pairs=selected, masked_keys=list(set(masked)))
