"""Tests for envault.env_backup.BackupManager."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.env_backup import BackupManager
from envault.exceptions import EnvaultError


@pytest.fixture()
def tmp_backup(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\n")
    config_dir = tmp_path / ".envault"
    manager = BackupManager(config_dir=config_dir)
    return manager, env_file


def test_create_backup_returns_path(tmp_backup):
    manager, env_file = tmp_backup
    dest = manager.create(env_file)
    assert dest.exists()
    assert dest.suffix == ".bak"


def test_create_backup_preserves_content(tmp_backup):
    manager, env_file = tmp_backup
    dest = manager.create(env_file)
    assert dest.read_text() == "KEY=value\n"


def test_create_missing_file_raises(tmp_backup):
    manager, _ = tmp_backup
    with pytest.raises(EnvaultError, match="Cannot backup missing file"):
        manager.create(Path("/nonexistent/.env"))


def test_list_backups_returns_newest_first(tmp_backup):
    manager, env_file = tmp_backup
    manager.create(env_file)
    time.sleep(0.01)
    manager.create(env_file)
    backups = manager.list_backups(env_file)
    assert len(backups) == 2
    assert backups[0].name > backups[1].name


def test_list_backups_empty_when_none_exist(tmp_backup):
    manager, env_file = tmp_backup
    assert manager.list_backups(env_file) == []


def test_restore_from_most_recent(tmp_backup):
    manager, env_file = tmp_backup
    manager.create(env_file)
    env_file.write_text("KEY=changed\n")
    manager.restore(env_file)
    assert env_file.read_text() == "KEY=value\n"


def test_restore_specific_backup(tmp_backup):
    manager, env_file = tmp_backup
    first = manager.create(env_file)
    env_file.write_text("KEY=v2\n")
    manager.create(env_file)
    env_file.write_text("KEY=v3\n")
    manager.restore(env_file, backup_path=first)
    assert env_file.read_text() == "KEY=value\n"


def test_restore_no_backups_raises(tmp_backup):
    manager, env_file = tmp_backup
    with pytest.raises(EnvaultError, match="No backups found"):
        manager.restore(env_file)


def test_delete_backup(tmp_backup):
    manager, env_file = tmp_backup
    dest = manager.create(env_file)
    manager.delete(dest)
    assert not dest.exists()


def test_delete_missing_backup_raises(tmp_backup):
    manager, _ = tmp_backup
    with pytest.raises(EnvaultError, match="Backup not found"):
        manager.delete(Path("/nonexistent/file.bak"))


def test_prune_keeps_max_backups(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("K=v\n")
    config_dir = tmp_path / ".envault"
    manager = BackupManager(config_dir=config_dir)
    manager.MAX_BACKUPS = 3
    for _ in range(5):
        manager.create(env_file)
        time.sleep(0.01)
    assert len(manager.list_backups(env_file)) == 3
