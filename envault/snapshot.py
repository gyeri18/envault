"""Snapshot manager for capturing and restoring .env file states."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from envault.exceptions import SnapshotError, VaultNotFoundError
from envault.vault import VaultManager


class SnapshotManager:
    """Manages point-in-time snapshots of encrypted vault contents."""

    def __init__(self, vault: VaultManager, config_dir: Optional[Path] = None):
        self.vault = vault
        self.config_dir = config_dir or Path.home() / ".envault"
        self._snapshots_dir = self.config_dir / "snapshots"
        self._ensure_snapshots_dir()

    def _ensure_snapshots_dir(self) -> None:
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _snapshot_path(self, project: str, label: str) -> Path:
        safe_label = label.replace("/", "_").replace(" ", "_")
        return self._snapshots_dir / f"{project}__{safe_label}.snap"

    def create(self, project: str, env_file: Path, label: Optional[str] = None, password: Optional[str] = None) -> str:
        """Create a snapshot of the current vault state."""
        if not env_file.exists():
            raise SnapshotError(f"Env file not found: {env_file}")

        label = label or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        snap_path = self._snapshot_path(project, label)

        if snap_path.exists():
            raise SnapshotError(f"Snapshot '{label}' already exists for project '{project}'")

        plaintext = env_file.read_text(encoding="utf-8")
        encrypted = self.vault.lock(project, plaintext, password=password)

        metadata = {
            "project": project,
            "label": label,
            "created_at": datetime.utcnow().isoformat(),
            "source": str(env_file),
            "ciphertext": encrypted,
        }
        snap_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return label

    def restore(self, project: str, label: str, output: Path, password: Optional[str] = None) -> None:
        """Restore a snapshot to the given output path."""
        snap_path = self._snapshot_path(project, label)
        if not snap_path.exists():
            raise SnapshotError(f"Snapshot '{label}' not found for project '{project}'")

        metadata = json.loads(snap_path.read_text(encoding="utf-8"))
        plaintext = self.vault.unlock(project, metadata["ciphertext"], password=password)
        output.write_text(plaintext, encoding="utf-8")

    def list_snapshots(self, project: str) -> list:
        """Return a list of snapshot metadata dicts for the given project."""
        results = []
        prefix = f"{project}__"
        for f in sorted(self._snapshots_dir.glob(f"{prefix}*.snap")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({"label": data["label"], "created_at": data["created_at"], "source": data["source"]})
            except (json.JSONDecodeError, KeyError):
                continue
        return results

    def delete(self, project: str, label: str) -> None:
        """Delete a named snapshot."""
        snap_path = self._snapshot_path(project, label)
        if not snap_path.exists():
            raise SnapshotError(f"Snapshot '{label}' not found for project '{project}'")
        snap_path.unlink()
