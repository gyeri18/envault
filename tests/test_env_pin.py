"""Tests for envault.env_pin.PinManager."""
import pytest
from pathlib import Path

from envault.env_pin import PinManager, PinError


@pytest.fixture()
def manager(tmp_path: Path) -> PinManager:
    return PinManager(config_dir=tmp_path)


def test_pin_creates_entry(manager: PinManager) -> None:
    manager.pin("myapp", "DATABASE_URL")
    assert "DATABASE_URL" in manager.list_pins("myapp")


def test_pin_multiple_keys(manager: PinManager) -> None:
    manager.pin("myapp", "DATABASE_URL")
    manager.pin("myapp", "SECRET_KEY")
    pins = manager.list_pins("myapp")
    assert "DATABASE_URL" in pins
    assert "SECRET_KEY" in pins


def test_pin_duplicate_raises(manager: PinManager) -> None:
    manager.pin("myapp", "DATABASE_URL")
    with pytest.raises(PinError, match="already pinned"):
        manager.pin("myapp", "DATABASE_URL")


def test_pin_empty_key_raises(manager: PinManager) -> None:
    with pytest.raises(PinError, match="must not be empty"):
        manager.pin("myapp", "")


def test_unpin_removes_key(manager: PinManager) -> None:
    manager.pin("myapp", "DATABASE_URL")
    manager.unpin("myapp", "DATABASE_URL")
    assert manager.list_pins("myapp") == []


def test_unpin_missing_key_raises(manager: PinManager) -> None:
    with pytest.raises(PinError, match="not pinned"):
        manager.unpin("myapp", "MISSING_KEY")


def test_unpin_removes_project_when_empty(manager: PinManager, tmp_path: Path) -> None:
    manager.pin("myapp", "KEY")
    manager.unpin("myapp", "KEY")
    # Reloading should return empty list, not raise
    assert manager.list_pins("myapp") == []


def test_list_pins_unknown_project_returns_empty(manager: PinManager) -> None:
    assert manager.list_pins("unknown") == []


def test_check_returns_missing_keys(manager: PinManager) -> None:
    manager.pin("myapp", "DATABASE_URL")
    manager.pin("myapp", "SECRET_KEY")
    missing = manager.check("myapp", ["DATABASE_URL"])
    assert missing == ["SECRET_KEY"]


def test_check_no_missing_returns_empty(manager: PinManager) -> None:
    manager.pin("myapp", "DATABASE_URL")
    missing = manager.check("myapp", ["DATABASE_URL", "EXTRA_KEY"])
    assert missing == []


def test_check_unknown_project_returns_empty(manager: PinManager) -> None:
    assert manager.check("ghost", ["ANY_KEY"]) == []


def test_pins_are_isolated_per_project(manager: PinManager) -> None:
    manager.pin("app1", "KEY_A")
    manager.pin("app2", "KEY_B")
    assert manager.list_pins("app1") == ["KEY_A"]
    assert manager.list_pins("app2") == ["KEY_B"]
