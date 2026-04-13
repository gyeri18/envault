"""Tests for envault.env_namespace."""

from __future__ import annotations

import pytest

from envault.env_namespace import NamespaceError, NamespaceManager


@pytest.fixture()
def manager(tmp_path):
    return NamespaceManager(tmp_path / ".envault")


def test_create_namespace_stores_entry(manager):
    manager.create("db", "DB_")
    entries = manager.list_namespaces()
    assert any(e["name"] == "db" and e["prefix"] == "DB_" for e in entries)


def test_create_duplicate_raises(manager):
    manager.create("db", "DB_")
    with pytest.raises(NamespaceError, match="already exists"):
        manager.create("db", "DB_")


def test_create_empty_name_raises(manager):
    with pytest.raises(NamespaceError, match="name must not be empty"):
        manager.create("", "DB_")


def test_create_empty_prefix_raises(manager):
    with pytest.raises(NamespaceError, match="Prefix must not be empty"):
        manager.create("db", "")


def test_get_prefix_returns_value(manager):
    manager.create("cache", "CACHE_")
    assert manager.get_prefix("cache") == "CACHE_"


def test_get_prefix_missing_raises(manager):
    with pytest.raises(NamespaceError, match="not found"):
        manager.get_prefix("nonexistent")


def test_delete_removes_entry(manager):
    manager.create("app", "APP_")
    manager.delete("app")
    assert not any(e["name"] == "app" for e in manager.list_namespaces())


def test_delete_missing_raises(manager):
    with pytest.raises(NamespaceError, match="not found"):
        manager.delete("ghost")


def test_list_is_sorted(manager):
    manager.create("zebra", "Z_")
    manager.create("alpha", "A_")
    names = [e["name"] for e in manager.list_namespaces()]
    assert names == sorted(names)


def test_keys_in_namespace_filters_correctly(manager):
    manager.create("db", "DB_")
    pairs = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_NAME": "myapp"}
    result = manager.keys_in_namespace("db", pairs)
    assert set(result.keys()) == {"DB_HOST", "DB_PORT"}
    assert "APP_NAME" not in result


def test_keys_in_namespace_empty_when_no_match(manager):
    manager.create("cache", "CACHE_")
    pairs = {"DB_HOST": "localhost", "APP_NAME": "myapp"}
    result = manager.keys_in_namespace("cache", pairs)
    assert result == {}
