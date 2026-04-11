"""Tests for envault.env_scope."""
from __future__ import annotations

import pytest

from envault.env_scope import ScopeError, ScopeManager


@pytest.fixture()
def manager(tmp_path):
    return ScopeManager(tmp_path / ".envault")


# --- create / basic retrieval ---

def test_create_scope_stores_keys(manager):
    manager.create("backend", ["DB_HOST", "DB_PORT"])
    assert manager.get("backend") == ["DB_HOST", "DB_PORT"]


def test_create_deduplicates_and_sorts(manager):
    manager.create("web", ["PORT", "HOST", "PORT"])
    assert manager.get("web") == ["HOST", "PORT"]


def test_create_empty_name_raises(manager):
    with pytest.raises(ScopeError, match="empty"):
        manager.create("", ["KEY"])


def test_create_empty_keys_raises(manager):
    with pytest.raises(ScopeError, match="at least one"):
        manager.create("empty", [])


# --- list / delete ---

def test_list_scopes_returns_sorted_names(manager):
    manager.create("z_scope", ["Z"])
    manager.create("a_scope", ["A"])
    assert manager.list_scopes() == ["a_scope", "z_scope"]


def test_list_scopes_empty_when_none(manager):
    assert manager.list_scopes() == []


def test_delete_removes_scope(manager):
    manager.create("tmp", ["X"])
    manager.delete("tmp")
    assert "tmp" not in manager.list_scopes()


def test_delete_nonexistent_raises(manager):
    with pytest.raises(ScopeError, match="does not exist"):
        manager.delete("ghost")


# --- apply ---

def test_apply_filters_env_pairs(manager):
    manager.create("frontend", ["API_URL", "FEATURE_FLAG"])
    env = {"API_URL": "https://api", "DB_PASS": "secret", "FEATURE_FLAG": "1"}
    result = manager.apply("frontend", env)
    assert result == {"API_URL": "https://api", "FEATURE_FLAG": "1"}


def test_apply_returns_empty_when_no_match(manager):
    manager.create("infra", ["AWS_KEY"])
    result = manager.apply("infra", {"DB_HOST": "localhost"})
    assert result == {}


# --- add_key / remove_key ---

def test_add_key_extends_scope(manager):
    manager.create("svc", ["HOST"])
    manager.add_key("svc", "PORT")
    assert "PORT" in manager.get("svc")


def test_add_duplicate_key_raises(manager):
    manager.create("svc", ["HOST"])
    with pytest.raises(ScopeError, match="already in scope"):
        manager.add_key("svc", "HOST")


def test_remove_key_shrinks_scope(manager):
    manager.create("svc", ["HOST", "PORT"])
    manager.remove_key("svc", "PORT")
    assert "PORT" not in manager.get("svc")


def test_remove_missing_key_raises(manager):
    manager.create("svc", ["HOST"])
    with pytest.raises(ScopeError, match="not in scope"):
        manager.remove_key("svc", "GHOST")


def test_remove_last_key_raises(manager):
    manager.create("svc", ["HOST"])
    with pytest.raises(ScopeError, match="last key"):
        manager.remove_key("svc", "HOST")
