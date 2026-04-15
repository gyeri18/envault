"""Detect unused keys in .env files by comparing against a reference pattern list."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


class UnusedError(Exception):
    """Raised when the unused-key scan cannot proceed."""


@dataclass
class UnusedResult:
    unused_keys: List[str] = field(default_factory=list)
    scanned_keys: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.unused_keys) == 0

    @property
    def summary(self) -> str:
        if self.ok:
            return "No unused keys detected."
        keys = ", ".join(self.unused_keys)
        return f"{len(self.unused_keys)} unused key(s): {keys}"


class UnusedManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"

    def _parse_env_file(self, path: Path) -> Set[str]:
        keys: Set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key:
                    keys.add(key)
        return keys

    def scan(
        self,
        env_file: Path,
        reference_file: Path,
    ) -> UnusedResult:
        """Return keys present in *env_file* but absent from *reference_file*.

        *reference_file* is treated as the source-of-truth list of keys that
        are actually consumed by the application (e.g. a .env.example or a
        generated reference listing).
        """
        env_path = Path(env_file)
        ref_path = Path(reference_file)

        if not env_path.exists():
            raise UnusedError(f"Env file not found: {env_path}")
        if not ref_path.exists():
            raise UnusedError(f"Reference file not found: {ref_path}")

        env_keys = self._parse_env_file(env_path)
        ref_keys = self._parse_env_file(ref_path)

        unused = sorted(env_keys - ref_keys)
        return UnusedResult(
            unused_keys=unused,
            scanned_keys=sorted(env_keys),
        )
