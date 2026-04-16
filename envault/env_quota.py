"""Quota management: enforce maximum number of keys in an env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class QuotaError(Exception):
    pass


@dataclass
class QuotaViolation:
    project: str
    current: int
    limit: int

    def __str__(self) -> str:
        return (
            f"[{self.project}] quota exceeded: {self.current} keys present, "
            f"limit is {self.limit}"
        )


@dataclass
class QuotaResult:
    violations: List[QuotaViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.ok:
            return "All projects within quota."
        lines = [str(v) for v in self.violations]
        return "\n".join(lines)


class QuotaManager:
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _quotas_path(self) -> Path:
        return self._config_dir / "quotas.json"

    def _load(self) -> Dict[str, int]:
        if not self._quotas_path.exists():
            return {}
        import json
        return json.loads(self._quotas_path.read_text())

    def _save(self, data: Dict[str, int]) -> None:
        import json
        self._quotas_path.write_text(json.dumps(data, indent=2))

    def set_quota(self, project: str, limit: int) -> None:
        if not project:
            raise QuotaError("Project name must not be empty.")
        if limit < 1:
            raise QuotaError("Quota limit must be at least 1.")
        data = self._load()
        data[project] = limit
        self._save(data)

    def remove_quota(self, project: str) -> None:
        data = self._load()
        if project not in data:
            raise QuotaError(f"No quota set for project '{project}'.")
        del data[project]
        self._save(data)

    def get_quota(self, project: str) -> Optional[int]:
        return self._load().get(project)

    def list_quotas(self) -> Dict[str, int]:
        return self._load()

    def check(self, project: str, env_file: Path) -> QuotaResult:
        limit = self.get_quota(project)
        if limit is None:
            return QuotaResult()
        count = _count_keys(env_file)
        violations: List[QuotaViolation] = []
        if count > limit:
            violations.append(QuotaViolation(project=project, current=count, limit=limit))
        return QuotaResult(violations=violations)


def _count_keys(env_file: Path) -> int:
    if not env_file.exists():
        raise QuotaError(f"File not found: {env_file}")
    count = 0
    for line in env_file.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            count += 1
    return count
