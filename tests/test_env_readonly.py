"""Tests for envault.env_readonly."""
from __future__ import annotations

import pytest

from envault.env_readonly import ReadonlyError, ReadonlyManager


@pytest.fixture()
def manager(tmp_path):
    return ReadonlyManager(config_dir=tmp_path / ".envault")


def _write(path, content):
    path.write_text(content)


# --- mark / unmark -----------------------------------------------------------

def test_mark_creates_entry(manager):
    manager.mark("SECRET_KEY")
    assert manager.is_readonly("SECRET_KEY")


def test_mark_multiple_keys(manager):
    manager.mark("KEY_A")
    manager.mark("KEY_B")
    assert manager.list_keys() == ["KEY_A", "KEY_B"]


def test_mark_duplicate_raises(manager):
    manager.mark("DB_PASS")
    with pytest.raises(ReadonlyError, match="already marked"):
        manager.mark("DB_PASS")


def test_mark_empty_key_raises(manager):
    with pytest.raises(ReadonlyError, match="empty"):
        manager.mark("")


def test_unmark_removes_entry(manager):
    manager.mark("TOKEN")
    manager.unmark("TOKEN")
    assert not manager.is_readonly("TOKEN")


def test_unmark_missing_key_raises(manager):
    with pytest.raises(ReadonlyError, match="not marked"):
        manager.unmark("NONEXISTENT")


# --- list_keys ---------------------------------------------------------------

def test_list_keys_returns_sorted(manager):
    manager.mark("ZEBRA")
    manager.mark("ALPHA")
    assert manager.list_keys() == ["ALPHA", "ZEBRA"]


def test_list_keys_empty(manager):
    assert manager.list_keys() == []


# --- is_readonly -------------------------------------------------------------

def test_is_readonly_false_for_unknown_key(manager):
    assert not manager.is_readonly("UNKNOWN")


# --- check -------------------------------------------------------------------

def test_check_raises_when_value_changed(manager, tmp_path):
    env_file = tmp_path / ".env"
    _write(env_file, "API_KEY=original_value\n")
    manager.mark("API_KEY")
    with pytest.raises(ReadonlyError, match="read-only"):
        manager.check("API_KEY", "new_value", env_file)


def test_check_passes_when_value_unchanged(manager, tmp_path):
    env_file = tmp_path / ".env"
    _write(env_file, "API_KEY=same_value\n")
    manager.mark("API_KEY")
    # Should not raise
    manager.check("API_KEY", "same_value", env_file)


def test_check_passes_for_non_readonly_key(manager, tmp_path):
    env_file = tmp_path / ".env"
    _write(env_file, "FREE_KEY=old\n")
    # Not marked — no error even with different value
    manager.check("FREE_KEY", "completely_different", env_file)


def test_check_passes_when_env_file_missing(manager, tmp_path):
    manager.mark("MISSING_FILE_KEY")
    # File doesn't exist — silently passes
    manager.check("MISSING_FILE_KEY", "any_value", tmp_path / "nonexistent.env")
