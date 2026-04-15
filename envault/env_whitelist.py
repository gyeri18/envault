"""Whitelist manager: restrict which keys are allowed in an env file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional


class WhitelistError(Exception):
    pass


class WhitelistViolation:
    def __init__(self, key: str):
        self.key = key

    def __str__(self) -> str:
        return f"Key not in whitelist: {self.key}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"WhitelistViolation(key={self.key!r})"


class WhitelistResult:
    def __init__(self, violations: List[WhitelistViolation]):
        self.violations = violations

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.ok:
            return "All keys are whitelisted."
        lines = [str(v) for v in self.violations]
        return "\n".join(lines)


class WhitelistManager:
    def __init__(self, config_dir: Optional[Path] = None):
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _whitelist_path(self, project: str) -> Path:
        return self._config_dir / f"whitelist_{project}.json"

    def set_whitelist(self, project: str, keys: List[str]) -> None:
        if not project:
            raise WhitelistError("Project name must not be empty.")
        if not keys:
            raise WhitelistError("Whitelist must contain at least one key.")
        cleaned = sorted(set(k.strip() for k in keys if k.strip()))
        self._whitelist_path(project).write_text(json.dumps(cleaned, indent=2))

    def get_whitelist(self, project: str) -> List[str]:
        path = self._whitelist_path(project)
        if not path.exists():
            raise WhitelistError(f"No whitelist found for project: {project}")
        return json.loads(path.read_text())

    def delete_whitelist(self, project: str) -> None:
        path = self._whitelist_path(project)
        if not path.exists():
            raise WhitelistError(f"No whitelist found for project: {project}")
        path.unlink()

    def check(self, project: str, env_file: Path) -> WhitelistResult:
        allowed = set(self.get_whitelist(project))
        violations: List[WhitelistViolation] = []
        for line in Path(env_file).read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key = stripped.split("=", 1)[0].strip()
            if key and key not in allowed:
                violations.append(WhitelistViolation(key))
        return WhitelistResult(violations)
