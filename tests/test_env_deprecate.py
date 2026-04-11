"""Tests for envault.env_deprecate."""
import pytest
from pathlib import Path

from envault.env_deprecate import DeprecateManager, DeprecateError, DeprecationEntry


@pytest.fixture
def manager(tmp_path: Path) -> DeprecateManager:
    return DeprecateManager(config_dir=tmp_path / ".envault")


def test_mark_creates_entry(manager: DeprecateManager) -> None:
    entry = manager.mark("OLD_KEY", "No longer used.")
    assert isinstance(entry, DeprecationEntry)
    assert entry.key == "OLD_KEY"
    assert entry.reason == "No longer used."
    assert entry.replacement is None


def test_mark_with_replacement(manager: DeprecateManager) -> None:
    entry = manager.mark("OLD_KEY", "Renamed.", replacement="NEW_KEY")
    assert entry.replacement == "NEW_KEY"


def test_mark_duplicate_raises(manager: DeprecateManager) -> None:
    manager.mark("OLD_KEY", "reason")
    with pytest.raises(DeprecateError, match="already marked"):
        manager.mark("OLD_KEY", "another reason")


def test_mark_empty_key_raises(manager: DeprecateManager) -> None:
    with pytest.raises(DeprecateError, match="empty"):
        manager.mark("", "reason")


def test_mark_empty_reason_raises(manager: DeprecateManager) -> None:
    with pytest.raises(DeprecateError, match="empty"):
        manager.mark("KEY", "")


def test_unmark_removes_entry(manager: DeprecateManager) -> None:
    manager.mark("OLD_KEY", "reason")
    manager.unmark("OLD_KEY")
    report = manager.list_deprecated()
    assert not report.has("OLD_KEY")


def test_unmark_missing_key_raises(manager: DeprecateManager) -> None:
    with pytest.raises(DeprecateError, match="not marked"):
        manager.unmark("GHOST")


def test_list_returns_all(manager: DeprecateManager) -> None:
    manager.mark("A", "reason A")
    manager.mark("B", "reason B", replacement="C")
    report = manager.list_deprecated()
    assert len(report.entries) == 2
    assert report.has("A")
    assert report.has("B")


def test_list_empty_when_none(manager: DeprecateManager) -> None:
    report = manager.list_deprecated()
    assert report.entries == []


def test_check_flags_deprecated_keys(manager: DeprecateManager) -> None:
    manager.mark("OLD_KEY", "reason")
    report = manager.check(["OLD_KEY", "FRESH_KEY"])
    assert report.has("OLD_KEY")
    assert not report.has("FRESH_KEY")


def test_check_returns_empty_when_no_match(manager: DeprecateManager) -> None:
    manager.mark("OLD_KEY", "reason")
    report = manager.check(["FRESH_KEY"])
    assert report.entries == []


def test_deprecation_entry_str_no_replacement() -> None:
    entry = DeprecationEntry(key="K", reason="gone")
    assert str(entry) == "K: gone"


def test_deprecation_entry_str_with_replacement() -> None:
    entry = DeprecationEntry(key="K", reason="renamed", replacement="NEW_K")
    assert "NEW_K" in str(entry)
