"""Tests for env_freeze module."""
import pytest
from pathlib import Path
from envault.env_freeze import FreezeManager, FreezeError


@pytest.fixture
def manager(tmp_path: Path) -> FreezeManager:
    return FreezeManager(config_dir=tmp_path)


def test_freeze_creates_entry(manager):
    manager.freeze("SECRET_KEY")
    assert manager.is_frozen("SECRET_KEY")


def test_freeze_with_reason(manager):
    manager.freeze("API_KEY", reason="production key")
    entries = manager.list_frozen()
    assert any(e["key"] == "API_KEY" and e["reason"] == "production key" for e in entries)


def test_freeze_duplicate_raises(manager):
    manager.freeze("DB_PASS")
    with pytest.raises(FreezeError, match="already frozen"):
        manager.freeze("DB_PASS")


def test_freeze_empty_key_raises(manager):
    with pytest.raises(FreezeError, match="empty"):
        manager.freeze("")


def test_unfreeze_removes_entry(manager):
    manager.freeze("TOKEN")
    manager.unfreeze("TOKEN")
    assert not manager.is_frozen("TOKEN")


def test_unfreeze_missing_key_raises(manager):
    with pytest.raises(FreezeError, match="not frozen"):
        manager.unfreeze("MISSING")


def test_list_frozen_returns_sorted(manager):
    manager.freeze("Z_KEY")
    manager.freeze("A_KEY")
    keys = [e["key"] for e in manager.list_frozen()]
    assert keys == ["A_KEY", "Z_KEY"]


def test_check_returns_frozen_subset(manager):
    manager.freeze("FROZEN_ONE")
    manager.freeze("FROZEN_TWO")
    result = manager.check(["FROZEN_ONE", "NOT_FROZEN", "FROZEN_TWO"])
    assert set(result) == {"FROZEN_ONE", "FROZEN_TWO"}


def test_check_empty_list(manager):
    assert manager.check([]) == []


def test_is_frozen_false_for_unknown(manager):
    assert not manager.is_frozen("UNKNOWN_KEY")
