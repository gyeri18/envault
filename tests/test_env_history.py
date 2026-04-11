"""Tests for envault.env_history."""
import pytest
from pathlib import Path

from envault.env_history import HistoryManager, HistoryEntry


@pytest.fixture
def manager(tmp_path: Path) -> HistoryManager:
    return HistoryManager(config_dir=tmp_path, project="myapp")


def test_history_dir_created(tmp_path: Path) -> None:
    HistoryManager(config_dir=tmp_path, project="p")
    assert (tmp_path / "history").is_dir()


def test_record_returns_entry(manager: HistoryManager) -> None:
    entry = manager.record(key="DB_URL", action="set", new_value="postgres://localhost")
    assert isinstance(entry, HistoryEntry)
    assert entry.key == "DB_URL"
    assert entry.action == "set"
    assert entry.project == "myapp"


def test_record_hashes_values(manager: HistoryManager) -> None:
    entry = manager.record(key="SECRET", action="set",
                           old_value="old", new_value="new")
    assert entry.old_value_hash is not None
    assert entry.new_value_hash is not None
    assert entry.old_value_hash != entry.new_value_hash
    assert len(entry.old_value_hash) == 12


def test_record_none_values_produce_none_hashes(manager: HistoryManager) -> None:
    entry = manager.record(key="X", action="delete", old_value="val")
    assert entry.old_value_hash is not None
    assert entry.new_value_hash is None


def test_get_entries_empty_when_no_history(manager: HistoryManager) -> None:
    assert manager.get_entries() == []


def test_get_entries_returns_all(manager: HistoryManager) -> None:
    manager.record("A", "set", new_value="1")
    manager.record("B", "set", new_value="2")
    entries = manager.get_entries()
    assert len(entries) == 2


def test_get_entries_filtered_by_key(manager: HistoryManager) -> None:
    manager.record("A", "set", new_value="1")
    manager.record("B", "set", new_value="2")
    manager.record("A", "rotate", old_value="1", new_value="3")
    entries = manager.get_entries(key="A")
    assert len(entries) == 2
    assert all(e.key == "A" for e in entries)


def test_invalid_action_raises(manager: HistoryManager) -> None:
    with pytest.raises(ValueError, match="Unknown action"):
        manager.record("KEY", "invalid")


def test_clear_removes_history(manager: HistoryManager) -> None:
    manager.record("X", "set", new_value="v")
    manager.clear()
    assert manager.get_entries() == []


def test_clear_no_error_when_no_file(manager: HistoryManager) -> None:
    manager.clear()  # should not raise


def test_str_representation(manager: HistoryManager) -> None:
    entry = manager.record("MY_KEY", "set", new_value="val")
    s = str(entry)
    assert "SET" in s
    assert "MY_KEY" in s
    assert "myapp" in s


def test_separate_projects_isolated(tmp_path: Path) -> None:
    m1 = HistoryManager(config_dir=tmp_path, project="proj1")
    m2 = HistoryManager(config_dir=tmp_path, project="proj2")
    m1.record("K", "set", new_value="v")
    assert m2.get_entries() == []
