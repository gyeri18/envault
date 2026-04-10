"""Statistics and summary reporting for .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.exceptions import EnvaultError


@dataclass
class EnvStats:
    total_keys: int = 0
    empty_values: int = 0
    commented_lines: int = 0
    blank_lines: int = 0
    duplicate_keys: List[str] = field(default_factory=list)
    longest_key: str = ""
    longest_value_key: str = ""
    key_lengths: Dict[str, int] = field(default_factory=dict)

    @property
    def unique_keys(self) -> int:
        return self.total_keys - len(self.duplicate_keys)

    def summary(self) -> str:
        lines = [
            f"Total keys      : {self.total_keys}",
            f"Unique keys     : {self.unique_keys}",
            f"Empty values    : {self.empty_values}",
            f"Duplicate keys  : {len(self.duplicate_keys)}",
            f"Commented lines : {self.commented_lines}",
            f"Blank lines     : {self.blank_lines}",
        ]
        if self.longest_key:
            lines.append(f"Longest key     : {self.longest_key} ({len(self.longest_key)} chars)")
        if self.longest_value_key:
            val_len = self.key_lengths.get(self.longest_value_key, 0)
            lines.append(f"Longest value   : {self.longest_value_key} ({val_len} chars)")
        return "\n".join(lines)


class StatsManager:
    def __init__(self, env_path: str | Path):
        self.env_path = Path(env_path)

    def compute(self) -> EnvStats:
        if not self.env_path.exists():
            raise EnvaultError(f"File not found: {self.env_path}")

        stats = EnvStats()
        seen: Dict[str, int] = {}
        value_lengths: Dict[str, int] = {}

        for raw_line in self.env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                stats.blank_lines += 1
                continue
            if line.startswith("#"):
                stats.commented_lines += 1
                continue
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)', line)
            if not match:
                continue
            key, value = match.group(1), match.group(2).strip('"\'')
            stats.total_keys += 1
            seen[key] = seen.get(key, 0) + 1
            if not value:
                stats.empty_values += 1
            value_lengths[key] = len(value)

        stats.duplicate_keys = [k for k, cnt in seen.items() if cnt > 1]
        if seen:
            stats.longest_key = max(seen.keys(), key=len)
        if value_lengths:
            stats.longest_value_key = max(value_lengths, key=lambda k: value_lengths[k])
            stats.key_lengths = value_lengths
        return stats
