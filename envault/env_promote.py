"""Promote env variables from one environment file to another."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class PromoteError(Exception):
    """Raised when a promotion operation fails."""


@dataclass
class PromoteResult:
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.promoted or self.overwritten)

    def summary(self) -> str:
        parts = []
        if self.promoted:
            parts.append(f"{len(self.promoted)} promoted")
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts) if parts else "nothing to promote"


class PromoteManager:
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self._config_dir = config_dir

    # ------------------------------------------------------------------
    def _parse_env_file(self, path: Path) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, _, value = stripped.partition("=")
                pairs[key.strip()] = value.strip()
        return pairs

    def _write_env_file(self, path: Path, pairs: Dict[str, str]) -> None:
        lines = [f"{k}={v}" for k, v in pairs.items()]
        path.write_text("\n".join(lines) + "\n")

    def promote(
        self,
        source: Path,
        destination: Path,
        keys: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> PromoteResult:
        if not source.exists():
            raise PromoteError(f"Source file not found: {source}")
        if not destination.exists():
            raise PromoteError(f"Destination file not found: {destination}")

        src_pairs = self._parse_env_file(source)
        dst_pairs = self._parse_env_file(destination)

        candidates = keys if keys is not None else list(src_pairs.keys())
        result = PromoteResult()

        for key in candidates:
            if key not in src_pairs:
                raise PromoteError(f"Key '{key}' not found in source file")
            if key in dst_pairs:
                if overwrite:
                    dst_pairs[key] = src_pairs[key]
                    result.overwritten.append(key)
                else:
                    result.skipped.append(key)
            else:
                dst_pairs[key] = src_pairs[key]
                result.promoted.append(key)

        if result.changed:
            self._write_env_file(destination, dst_pairs)

        return result
