"""Unit tests for envault.env_access."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_access import AccessManager, AccessEntry, AccessError


@pytest.fixture()
def manager(tmp_path: Path) -> AccessManager:
    return AccessManager(config_dir=tmp_path)


# ---------------------------------------------------------------------------
# AccessEntry
# ---------------------------------------------------------------------------

def test_entry_str():
    e = AccessEntry("dev", ["DB_URL", "API_KEY"])
    assert "dev" in str(e)
    assert "API_KEY" in str(e)


def test_entry_to_dict_round_trip():
    e = AccessEntry("admin", ["SECRET", "TOKEN"])
    d = e.to_dict()
    e2 = AccessEntry.from_dict(d)
    assert e2.role == "admin"
    assert e2.keys == ["SECRET", "TOKEN"]


# ---------------------------------------------------------------------------
# grant
# ---------------------------------------------------------------------------

def test_grant_creates_entry(manager: AccessManager):
    entry = manager.grant("dev", ["DB_URL"])
    assert entry.role == "dev"
    assert "DB_URL" in entry.keys


def test_grant_merges_with_existing(manager: AccessManager):
    manager.grant("dev", ["DB_URL"])
    entry = manager.grant("dev", ["API_KEY"])
    assert "DB_URL" in entry.keys
    assert "API_KEY" in entry.keys


def test_grant_deduplicates_keys(manager: AccessManager):
    entry = manager.grant("dev", ["DB_URL", "DB_URL"])
    assert entry.keys.count("DB_URL") == 1


def test_grant_empty_role_raises(manager: AccessManager):
    with pytest.raises(AccessError):
        manager.grant("", ["DB_URL"])


def test_grant_empty_keys_raises(manager: AccessManager):
    with pytest.raises(AccessError):
        manager.grant("dev", [])


# ---------------------------------------------------------------------------
# revoke
# ---------------------------------------------------------------------------

def test_revoke_removes_key(manager: AccessManager):
    manager.grant("dev", ["DB_URL", "API_KEY"])
    entry = manager.revoke("dev", ["DB_URL"])
    assert "DB_URL" not in entry.keys
    assert "API_KEY" in entry.keys


def test_revoke_missing_role_raises(manager: AccessManager):
    with pytest.raises(AccessError):
        manager.revoke("ghost", ["DB_URL"])


# ---------------------------------------------------------------------------
# can_access / allowed_keys
# ---------------------------------------------------------------------------

def test_can_access_returns_true(manager: AccessManager):
    manager.grant("ops", ["SECRET"])
    assert manager.can_access("ops", "SECRET") is True


def test_can_access_returns_false_for_unknown_key(manager: AccessManager):
    manager.grant("ops", ["SECRET"])
    assert manager.can_access("ops", "OTHER") is False


def test_can_access_returns_false_for_unknown_role(manager: AccessManager):
    assert manager.can_access("nobody", "SECRET") is False


def test_allowed_keys_returns_list(manager: AccessManager):
    manager.grant("qa", ["A", "B"])
    keys = manager.allowed_keys("qa")
    assert set(keys) == {"A", "B"}


# ---------------------------------------------------------------------------
# list_roles / delete_role
# ---------------------------------------------------------------------------

def test_list_roles_returns_sorted(manager: AccessManager):
    manager.grant("zebra", ["X"])
    manager.grant("alpha", ["Y"])
    roles = manager.list_roles()
    assert roles == ["alpha", "zebra"]


def test_delete_role_removes_entry(manager: AccessManager):
    manager.grant("temp", ["KEY"])
    manager.delete_role("temp")
    assert "temp" not in manager.list_roles()


def test_delete_missing_role_raises(manager: AccessManager):
    with pytest.raises(AccessError):
        manager.delete_role("nonexistent")
