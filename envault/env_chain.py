"""Chain multiple .env files with override precedence."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ChainError(Exception):
    """Raised when chaining fails."""


@dataclass
class ChainResult:
    merged: Dict[str, str] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)  # key -> file that won

    @property
    def key_count(self) -> int:
        return len(self.merged)


class ChainManager:
    """Merge a list of .env files with later files taking precedence."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def _parse_env_file(self, path: Path) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                pairs[key] = value
        return pairs

    def chain(self, files: List[str | Path]) -> ChainResult:
        """Merge files in order; later files override earlier ones."""
        if not files:
            raise ChainError("At least one file must be provided.")

        result = ChainResult()
        for raw_path in files:
            path = Path(raw_path)
            if not path.is_absolute():
                path = self.base_dir / path
            if not path.exists():
                raise ChainError(f"File not found: {path}")
            pairs = self._parse_env_file(path)
            for key, value in pairs.items():
                result.merged[key] = value
                result.sources[key] = str(path)
        return result

    def write(self, result: ChainResult, dest: str | Path) -> Path:
        """Write the merged result to *dest* as a .env file."""
        dest = Path(dest)
        lines = [f"{k}={v}" for k, v in sorted(result.merged.items())]
        dest.write_text("\n".join(lines) + "\n")
        return dest
