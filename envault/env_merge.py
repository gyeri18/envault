"""Merge two .env files with conflict resolution strategies."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

from envault.exceptions import EnvaultError


class MergeStrategy(str, Enum):
    OURS = "ours"       # keep current value on conflict
    THEIRS = "theirs"   # take incoming value on conflict
    PROMPT = "prompt"   # raise ConflictError listing conflicts


class MergeConflict:
    def __init__(self, key: str, ours: str, theirs: str) -> None:
        self.key = key
        self.ours = ours
        self.theirs = theirs

    def __repr__(self) -> str:  # pragma: no cover
        return f"MergeConflict(key={self.key!r}, ours={self.ours!r}, theirs={self.theirs!r})"


class MergeConflictError(EnvaultError):
    def __init__(self, conflicts: List[MergeConflict]) -> None:
        self.conflicts = conflicts
        keys = ", ".join(c.key for c in conflicts)
        super().__init__(f"Merge conflicts on keys: {keys}")


class MergeResult:
    def __init__(self, merged: Dict[str, str], conflicts: List[MergeConflict]) -> None:
        self.merged = merged
        self.conflicts = conflicts


class EnvMergeManager:
    """Merge two .env files into a destination file."""

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def merge(
        self,
        base_path: Path,
        incoming_path: Path,
        output_path: Path,
        strategy: MergeStrategy = MergeStrategy.OURS,
    ) -> MergeResult:
        base = self._parse(base_path)
        incoming = self._parse(incoming_path)
        merged, conflicts = self._resolve(base, incoming, strategy)
        self._write(output_path, merged)
        return MergeResult(merged=merged, conflicts=conflicts)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _parse(self, path: Path) -> Dict[str, str]:
        if not path.exists():
            raise EnvaultError(f"File not found: {path}")
        result: Dict[str, str] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip('"').strip("'")
        return result

    def _resolve(
        self,
        base: Dict[str, str],
        incoming: Dict[str, str],
        strategy: MergeStrategy,
    ) -> Tuple[Dict[str, str], List[MergeConflict]]:
        merged = dict(base)
        conflicts: List[MergeConflict] = []
        for key, value in incoming.items():
            if key not in base:
                merged[key] = value
            elif base[key] != value:
                conflicts.append(MergeConflict(key, base[key], value))
                if strategy == MergeStrategy.THEIRS:
                    merged[key] = value
                elif strategy == MergeStrategy.PROMPT:
                    pass  # will raise after collecting all
                # OURS: keep existing value (already in merged)
        if strategy == MergeStrategy.PROMPT and conflicts:
            raise MergeConflictError(conflicts)
        return merged, conflicts

    def _write(self, path: Path, data: Dict[str, str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{k}={v}" for k, v in data.items()]
        path.write_text("\n".join(lines) + "\n")
