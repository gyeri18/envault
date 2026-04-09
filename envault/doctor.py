"""Doctor module: checks envault project health and reports issues."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.storage import StorageManager


@dataclass
class DoctorIssue:
    level: str  # 'error' | 'warning' | 'info'
    message: str

    def __str__(self) -> str:
        icons = {"error": "✗", "warning": "⚠", "info": "ℹ"}
        return f"{icons.get(self.level, '?')} [{self.level.upper()}] {self.message}"


@dataclass
class DoctorReport:
    issues: List[DoctorIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.level == "warning" for i in self.issues)

    @property
    def ok(self) -> bool:
        return not self.has_errors and not self.has_warnings


class DoctorManager:
    def __init__(self, storage: StorageManager | None = None, config_dir: str | None = None):
        self.storage = storage or StorageManager(config_dir=config_dir)

    def check(self, project: str, env_file: str = ".env") -> DoctorReport:
        report = DoctorReport()

        # Check project key exists
        key = self.storage.get_project_key(project)
        if key is None:
            report.issues.append(
                DoctorIssue("error", f"No encryption key found for project '{project}'. Run 'envault init'.")
            )
        else:
            if len(key) < 32:
                report.issues.append(
                    DoctorIssue("warning", f"Project key for '{project}' appears shorter than expected.")
                )

        # Check .env file presence
        env_path = Path(env_file)
        if not env_path.exists():
            report.issues.append(
                DoctorIssue("warning", f"Environment file '{env_file}' not found in current directory.")
            )
        else:
            if env_path.stat().st_size == 0:
                report.issues.append(
                    DoctorIssue("info", f"Environment file '{env_file}' is empty.")
                )

        # Check vault file presence
        vault_file = Path(f"{env_file}.vault")
        if not vault_file.exists():
            report.issues.append(
                DoctorIssue("info", f"No vault file found ('{vault_file}'). File has not been locked yet.")
            )

        # Check config dir permissions
        config_dir = Path(self.storage.config_dir)
        if config_dir.exists() and not os.access(config_dir, os.W_OK):
            report.issues.append(
                DoctorIssue("error", f"Config directory '{config_dir}' is not writable.")
            )

        if report.ok:
            report.issues.append(
                DoctorIssue("info", f"Project '{project}' looks healthy.")
            )

        return report
