"""Automatic backup management for .env files before destructive operations."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from envault.exceptions import EnvaultError


class BackupManager:
    """Manages timestamped backups of .env files."""

    BACKUP_SUFFIX = ".bak"
    MAX_BACKUPS = 10

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self._config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._backups_dir = self._config_dir / "backups"
        self._ensure_backups_dir()

    def _ensure_backups_dir(self) -> None:
        self._backups_dir.mkdir(parents=True, exist_ok=True)

    def _backup_path(self, env_file: Path, timestamp: str) -> Path:
        safe_name = env_file.resolve().as_posix().replace("/", "_").lstrip("_")
        return self._backups_dir / f"{safe_name}__{timestamp}{self.BACKUP_SUFFIX}"

    def create(self, env_file: Path) -> Path:
        """Create a timestamped backup of *env_file*. Returns the backup path."""
        env_file = Path(env_file)
        if not env_file.exists():
            raise EnvaultError(f"Cannot backup missing file: {env_file}")

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        dest = self._backup_path(env_file, timestamp)
        shutil.copy2(env_file, dest)
        self._prune(env_file)
        return dest

    def list_backups(self, env_file: Path) -> List[Path]:
        """Return all backups for *env_file*, newest first."""
        env_file = Path(env_file)
        safe_name = env_file.resolve().as_posix().replace("/", "_").lstrip("_")
        pattern = f"{safe_name}__*{self.BACKUP_SUFFIX}"
        backups = sorted(self._backups_dir.glob(pattern), reverse=True)
        return backups

    def restore(self, env_file: Path, backup_path: Optional[Path] = None) -> Path:
        """Restore *env_file* from *backup_path* (or the most recent backup)."""
        env_file = Path(env_file)
        if backup_path is None:
            candidates = self.list_backups(env_file)
            if not candidates:
                raise EnvaultError(f"No backups found for {env_file}")
            backup_path = candidates[0]

        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise EnvaultError(f"Backup file not found: {backup_path}")

        shutil.copy2(backup_path, env_file)
        return env_file

    def delete(self, backup_path: Path) -> None:
        """Delete a specific backup file."""
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise EnvaultError(f"Backup not found: {backup_path}")
        backup_path.unlink()

    def _prune(self, env_file: Path) -> None:
        """Remove oldest backups exceeding MAX_BACKUPS for *env_file*."""
        backups = self.list_backups(env_file)
        for old in backups[self.MAX_BACKUPS :]:
            old.unlink(missing_ok=True)
