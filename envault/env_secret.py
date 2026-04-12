"""Secret detection: scan .env files for high-entropy or pattern-matched values."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# Patterns that strongly suggest a value is a secret
_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)"),
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),  # base64-ish long strings
    re.compile(r"[0-9a-fA-F]{32,}"),           # hex strings (e.g. MD5/SHA)
]

_ENTROPY_THRESHOLD = 3.8  # Shannon entropy threshold


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    freq = {c: value.count(c) / len(value) for c in set(value)}
    return -sum(p * math.log2(p) for p in freq.values())


@dataclass
class SecretFinding:
    line_number: int
    key: str
    reason: str

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.key!r} — {self.reason}"


@dataclass
class SecretScanResult:
    findings: List[SecretFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.findings) == 0

    def summary(self) -> str:
        if self.ok:
            return "No secrets detected."
        return f"{len(self.findings)} potential secret(s) detected."


class SecretError(Exception):
    pass


class SecretManager:
    def __init__(self, entropy_threshold: float = _ENTROPY_THRESHOLD) -> None:
        self.entropy_threshold = entropy_threshold

    def scan(self, env_file: Path) -> SecretScanResult:
        if not env_file.exists():
            raise SecretError(f"File not found: {env_file}")

        result = SecretScanResult()
        for lineno, raw in enumerate(env_file.read_text().splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"\'')
            if not value:
                continue

            reason: Optional[str] = None
            for pattern in _PATTERNS:
                if pattern.search(key) or pattern.search(value):
                    reason = f"matches pattern /{pattern.pattern}/"
                    break

            if reason is None:
                entropy = _shannon_entropy(value)
                if entropy >= self.entropy_threshold:
                    reason = f"high entropy ({entropy:.2f})"

            if reason:
                result.findings.append(SecretFinding(lineno, key, reason))

        return result
