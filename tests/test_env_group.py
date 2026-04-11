"""Tests for envault.env_group."""
import pytest
from pathlib import Path

from envault.env_group import GroupManager, GroupError


@pytest.fixture()
def manager(tmp_path: Path) -> GroupManager:
    return GroupManager(tmp_path / ".envault")


def test_create_group_stores_keys(manager: GroupManager) -> None:
    manager.create("db", ["DB_HOST", "DB_PORT"])
    assert manager.get("db") == ["DB_HOST", "DB_PORT"]


def test_create_deduplicates_and_sorts(manager: GroupManager) -> None:
    manager.create("web", ["PORT", "HOST", "PORT"])
    assert manager.get("web") == ["HOST", "PORT"]


def test_create_empty_name_raises(manager: GroupManager) -> None:
    with pytest.raises(GroupError, match="empty"):
        manager.create("  ", ["KEY"])


def test_create_empty_keys_raises(manager: GroupManager) -> None:
    with pytest.raises(GroupError, match="at least one key"):
        manager.create("grp", [])


def test_create_duplicate_name_raises(manager: GroupManager) -> None:
    manager.create("grp", ["A"])
    with pytest.raises(GroupError, match="already exists"):
        manager.create("grp", ["B"])


def test_delete_removes_group(manager: GroupManager) -> None:
    manager.create("grp", ["A"])
    manager.delete("grp")
    assert "grp" not in manager.list_groups()


def test_delete_missing_group_raises(manager: GroupManager) -> None:
    with pytest.raises(GroupError, match="does not exist"):
        manager.delete("ghost")


def test_list_groups_sorted(manager: GroupManager) -> None:
    manager.create("zebra", ["Z"])
    manager.create("alpha", ["A"])
    assert manager.list_groups() == ["alpha", "zebra"]


def test_list_groups_empty(manager: GroupManager) -> None:
    assert manager.list_groups() == []


def test_add_key_appends(manager: GroupManager) -> None:
    manager.create("grp", ["A"])
    manager.add_key("grp", "B")
    assert "B" in manager.get("grp")


def test_add_key_duplicate_raises(manager: GroupManager) -> None:
    manager.create("grp", ["A"])
    with pytest.raises(GroupError, match="already in group"):
        manager.add_key("grp", "A")


def test_add_key_empty_raises(manager: GroupManager) -> None:
    manager.create("grp", ["A"])
    with pytest.raises(GroupError, match="empty"):
        manager.add_key("grp", "")


def test_add_key_missing_group_raises(manager: GroupManager) -> None:
    with pytest.raises(GroupError, match="does not exist"):
        manager.add_key("ghost", "KEY")


def test_remove_key_removes(manager: GroupManager) -> None:
    manager.create("grp", ["A", "B"])
    manager.remove_key("grp", "A")
    assert manager.get("grp") == ["B"]


def test_remove_key_missing_raises(manager: GroupManager) -> None:
    manager.create("grp", ["A"])
    with pytest.raises(GroupError, match="not in group"):
        manager.remove_key("grp", "Z")
