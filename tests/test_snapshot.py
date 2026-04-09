"""Tests for the SnapshotManager."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envault.snapshot import SnapshotManager
from envault.exceptions import SnapshotError


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=supersecret\n"


@pytest.fixture
def tmp_snap(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)

    vault = MagicMock()
    vault.lock.return_value = "encrypted_blob"
    vault.unlock.return_value = ENV_CONTENT

    manager = SnapshotManager(vault=vault, config_dir=tmp_path)
    return manager, env_file, vault, tmp_path


def test_create_snapshot_returns_label(tmp_snap):
    manager, env_file, vault, _ = tmp_snap
    label = manager.create("myproject", env_file, label="v1")
    assert label == "v1"
    vault.lock.assert_called_once()


def test_create_snapshot_file_exists(tmp_snap):
    manager, env_file, _, tmp_path = tmp_snap
    manager.create("myproject", env_file, label="v1")
    snap_file = tmp_path / "snapshots" / "myproject__v1.snap"
    assert snap_file.exists()


def test_create_duplicate_label_raises(tmp_snap):
    manager, env_file, _, _ = tmp_snap
    manager.create("myproject", env_file, label="v1")
    with pytest.raises(SnapshotError, match="already exists"):
        manager.create("myproject", env_file, label="v1")


def test_create_missing_env_file_raises(tmp_snap):
    manager, _, _, tmp_path = tmp_snap
    with pytest.raises(SnapshotError, match="not found"):
        manager.create("myproject", tmp_path / "nonexistent.env", label="v1")


def test_restore_writes_content(tmp_snap, tmp_path):
    manager, env_file, _, _ = tmp_snap
    manager.create("myproject", env_file, label="v1")
    output = tmp_path / "restored.env"
    manager.restore("myproject", "v1", output)
    assert output.read_text() == ENV_CONTENT


def test_restore_missing_snapshot_raises(tmp_snap, tmp_path):
    manager, _, _, _ = tmp_snap
    with pytest.raises(SnapshotError, match="not found"):
        manager.restore("myproject", "ghost", tmp_path / "out.env")


def test_list_snapshots_returns_metadata(tmp_snap):
    manager, env_file, _, _ = tmp_snap
    manager.create("myproject", env_file, label="v1")
    manager.create("myproject", env_file, label="v2")
    snapshots = manager.list_snapshots("myproject")
    labels = [s["label"] for s in snapshots]
    assert "v1" in labels
    assert "v2" in labels


def test_list_snapshots_empty_for_unknown_project(tmp_snap):
    manager, _, _, _ = tmp_snap
    assert manager.list_snapshots("ghost_project") == []


def test_delete_snapshot_removes_file(tmp_snap):
    manager, env_file, _, tmp_path = tmp_snap
    manager.create("myproject", env_file, label="v1")
    manager.delete("myproject", "v1")
    snap_file = tmp_path / "snapshots" / "myproject__v1.snap"
    assert not snap_file.exists()


def test_delete_missing_snapshot_raises(tmp_snap):
    manager, _, _, _ = tmp_snap
    with pytest.raises(SnapshotError, match="not found"):
        manager.delete("myproject", "ghost")
