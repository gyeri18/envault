"""Tests for envault.env_default."""
from __future__ import annotations

import pytest

from envault.env_default import DefaultEntry, DefaultError, DefaultManager


@pytest.fixture
def manager(tmp_path):
    return DefaultManager(config_dir=tmp_path)


def test_set_creates_entry(manager):
    entry = manager.set("DB_HOST", "localhost")
    assert isinstance(entry, DefaultEntry)
    assert entry.key == "DB_HOST"
    assert entry.value == "localhost"


def test_set_multiple_keys(manager):
    manager.set("A", "1")
    manager.set("B", "2")
    entries = manager.list_defaults()
    assert len(entries) == 2


def test_set_overwrites_existing(manager):
    manager.set("KEY", "old")
    manager.set("KEY", "new")
    assert manager.get("KEY") == "new"


def test_set_empty_key_raises(manager):
    with pytest.raises(DefaultError, match="empty"):
        manager.set("", "value")


def test_get_returns_none_for_missing(manager):
    assert manager.get("NONEXISTENT") is None


def test_get_returns_value_for_existing(manager):
    manager.set("PORT", "5432")
    assert manager.get("PORT") == "5432"


def test_remove_deletes_entry(manager):
    manager.set("TEMP", "yes")
    manager.remove("TEMP")
    assert manager.get("TEMP") is None


def test_remove_missing_key_raises(manager):
    with pytest.raises(DefaultError, match="No default"):
        manager.remove("GHOST")


def test_list_defaults_sorted(manager):
    manager.set("Z_KEY", "z")
    manager.set("A_KEY", "a")
    entries = manager.list_defaults()
    assert entries[0].key == "A_KEY"
    assert entries[1].key == "Z_KEY"


def test_apply_fills_missing_keys(manager):
    manager.set("HOST", "localhost")
    manager.set("PORT", "8080")
    result = manager.apply({"HOST": "prod.example.com"})
    assert result["HOST"] == "prod.example.com"  # existing not overwritten
    assert result["PORT"] == "8080"  # missing filled in


def test_apply_fills_empty_string_values(manager):
    manager.set("LOGLEVEL", "info")
    result = manager.apply({"LOGLEVEL": ""})
    assert result["LOGLEVEL"] == "info"


def test_default_entry_str(manager):
    entry = manager.set("FOO", "bar")
    assert str(entry) == "FOO=bar"


def test_defaults_persist_across_instances(tmp_path):
    m1 = DefaultManager(config_dir=tmp_path)
    m1.set("PERSIST", "yes")
    m2 = DefaultManager(config_dir=tmp_path)
    assert m2.get("PERSIST") == "yes"
