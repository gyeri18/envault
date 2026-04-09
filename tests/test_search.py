"""Tests for envault.search.SearchManager."""

from __future__ import annotations

import pytest

from unittest.mock import MagicMock
from envault.search import SearchManager
from envault.exceptions import VaultError


ENV_DATA = {
    "DATABASE_URL": "postgres://localhost/db",
    "DATABASE_POOL_SIZE": "5",
    "REDIS_URL": "redis://localhost",
    "SECRET_KEY": "supersecret",
    "DEBUG": "true",
}


@pytest.fixture()
def manager():
    vault = MagicMock()
    vault.unlock.return_value = ENV_DATA
    return SearchManager(vault=vault)


def test_glob_pattern_matches(manager):
    results = manager.search("myapp", "DATABASE_*", key=b"k")
    assert "DATABASE_URL" in results
    assert "DATABASE_POOL_SIZE" in results
    assert "REDIS_URL" not in results


def test_glob_no_match_returns_empty(manager):
    results = manager.search("myapp", "NONEXISTENT_*", key=b"k")
    assert results == {}


def test_regex_pattern_matches(manager):
    results = manager.search("myapp", r".*_URL$", key=b"k", use_regex=True)
    assert "DATABASE_URL" in results
    assert "REDIS_URL" in results
    assert "SECRET_KEY" not in results


def test_invalid_regex_raises(manager):
    with pytest.raises(VaultError, match="Invalid regex"):
        manager.search("myapp", "[invalid", key=b"k", use_regex=True)


def test_keys_only_returns_empty_values(manager):
    results = manager.search("myapp", "DATABASE_*", key=b"k", keys_only=True)
    assert all(v == "" for v in results.values())
    assert "DATABASE_URL" in results


def test_list_keys_returns_sorted(manager):
    keys = manager.list_keys("myapp", key=b"k")
    assert keys == sorted(ENV_DATA.keys())


def test_exact_glob_match(manager):
    results = manager.search("myapp", "DEBUG", key=b"k")
    assert results == {"DEBUG": "true"}


def test_vault_unlock_called_with_correct_args(manager):
    manager.search("myapp", "*", password="pass123")
    manager.vault.unlock.assert_called_with("myapp", key=None, password="pass123")
