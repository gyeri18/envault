"""Generate random values for .env file keys."""
from __future__ import annotations

import secrets
import string
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from envault.exceptions import EnvaultError


class GenerateError(EnvaultError):
    """Raised when value generation fails."""


@dataclass
class GenerateResult:
    generated: dict[str, str] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)


class GenerateManager:
    ALPHABETS = {
        "hex": string.hexdigits[:16],
        "alphanumeric": string.ascii_letters + string.digits,
        "alpha": string.ascii_letters,
        "numeric": string.digits,
        "printable": string.ascii_letters + string.digits + string.punctuation,
    }

    def __init__(self, env_path: Path) -> None:
        self.env_path = Path(env_path)

    def generate(
        self,
        keys: list[str],
        length: int = 32,
        charset: str = "hex",
        overwrite: bool = False,
    ) -> GenerateResult:
        """Generate random values for the given keys in the .env file."""
        if length < 1 or length > 512:
            raise GenerateError(f"Length must be between 1 and 512, got {length}")
        if charset not in self.ALPHABETS:
            raise GenerateError(
                f"Unknown charset '{charset}'. Choose from: {', '.join(self.ALPHABETS)}"
            )

        alphabet = self.ALPHABETS[charset]
        existing = self._parse_env_file()
        result = GenerateResult()

        for key in keys:
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                raise GenerateError(f"Invalid key name: '{key}'")
            if key in existing and not overwrite:
                result.skipped.append(key)
                continue
            value = "".join(secrets.choice(alphabet) for _ in range(length))
            existing[key] = value
            result.generated[key] = value

        self._write_env_file(existing)
        return result

    def _parse_env_file(self) -> dict[str, str]:
        pairs: dict[str, str] = {}
        if not self.env_path.exists():
            return pairs
        for line in self.env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip().strip('"').strip("'")
        return pairs

    def _write_env_file(self, pairs: dict[str, str]) -> None:
        lines = [f"{k}={v}" for k, v in pairs.items()]
        self.env_path.write_text("\n".join(lines) + ("\n" if lines else ""))
