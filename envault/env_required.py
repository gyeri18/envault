"""Check and enforce required keys in .env files."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class RequiredError(Exception):
    """Raised when a required-keys operation fails."""


@dataclass
class MissingKeyResult:
    missing: List[str] = field(default_factory=list)
    present: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0

    def summary(self) -> str:
        lines = [f"Present : {len(self.present)}", f"Missing : {len(self.missing)}"]
        if self.missing:
            lines.append("Missing keys: " + ", ".join(self.missing))
        return "\n".join(lines)


class RequiredManager:
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _required_path(self, project: str) -> Path:
        return self._config_dir / f"{project}.required.json"

    def set_required(self, project: str, keys: List[str]) -> None:
        if not project:
            raise RequiredError("Project name must not be empty.")
        if not keys:
            raise RequiredError("Keys list must not be empty.")
        data = sorted(set(keys))
        self._required_path(project).write_text(json.dumps(data, indent=2))

    def get_required(self, project: str) -> List[str]:
        path = self._required_path(project)
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def check(self, project: str, env_file: Path) -> MissingKeyResult:
        if not env_file.exists():
            raise RequiredError(f"Env file not found: {env_file}")
        required = self.get_required(project)
        present_keys: List[str] = []
        for line in env_file.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                present_keys.append(key)
        present_set = set(present_keys)
        missing = [k for k in required if k not in present_set]
        present = [k for k in required if k in present_set]
        return MissingKeyResult(missing=missing, present=present)

    def remove_required(self, project: str) -> bool:
        path = self._required_path(project)
        if path.exists():
            path.unlink()
            return True
        return False
