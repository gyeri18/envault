"""Compare two .env files or vault snapshots and report differences."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.exceptions import EnvaultError


@dataclass
class CompareResult:
    only_in_a: Dict[str, str] = field(default_factory=dict)
    only_in_b: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (val_a, val_b)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_a or self.only_in_b or self.changed)

    def summary(self) -> str:
        lines = []
        for k, v in sorted(self.only_in_a.items()):
            lines.append(f"- {k}={v}")
        for k, v in sorted(self.only_in_b.items()):
            lines.append(f"+ {k}={v}")
        for k, (va, vb) in sorted(self.changed.items()):
            lines.append(f"~ {k}: {va!r} -> {vb!r}")
        if not lines:
            lines.append("No differences found.")
        return "\n".join(lines)


class CompareManager:
    def __init__(self, redact: bool = False) -> None:
        self.redact = redact

    def _parse_env(self, path: Path) -> Dict[str, str]:
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
            result[key.strip()] = value.strip()
        return result

    def _maybe_redact(self, value: str) -> str:
        return "***" if self.redact else value

    def compare_files(self, path_a: Path, path_b: Path) -> CompareResult:
        env_a = self._parse_env(path_a)
        env_b = self._parse_env(path_b)
        return self._compare_dicts(env_a, env_b)

    def compare_dicts(
        self,
        env_a: Dict[str, str],
        env_b: Dict[str, str],
    ) -> CompareResult:
        return self._compare_dicts(env_a, env_b)

    def _compare_dicts(
        self,
        env_a: Dict[str, str],
        env_b: Dict[str, str],
    ) -> CompareResult:
        result = CompareResult()
        all_keys = set(env_a) | set(env_b)
        for key in sorted(all_keys):
            in_a = key in env_a
            in_b = key in env_b
            if in_a and not in_b:
                result.only_in_a[key] = self._maybe_redact(env_a[key])
            elif in_b and not in_a:
                result.only_in_b[key] = self._maybe_redact(env_b[key])
            elif env_a[key] != env_b[key]:
                result.changed[key] = (
                    self._maybe_redact(env_a[key]),
                    self._maybe_redact(env_b[key]),
                )
            else:
                result.unchanged.append(key)
        return result
