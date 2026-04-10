"""Tests for envault.env_alias.AliasManager."""
import pytest

from envault.env_alias import AliasError, AliasManager


@pytest.fixture()
def manager(tmp_path):
    return AliasManager(tmp_path)


# ---------------------------------------------------------------------------
# add / resolve
# ---------------------------------------------------------------------------

def test_add_creates_alias(manager):
    manager.add("db", "DATABASE_URL")
    assert manager.resolve("db") == "DATABASE_URL"


def test_add_duplicate_alias_raises(manager):
    manager.add("db", "DATABASE_URL")
    with pytest.raises(AliasError, match="already exists"):
        manager.add("db", "ANOTHER_KEY")


def test_add_empty_alias_raises(manager):
    with pytest.raises(AliasError, match="non-empty"):
        manager.add("", "DATABASE_URL")


def test_add_empty_key_raises(manager):
    with pytest.raises(AliasError, match="non-empty"):
        manager.add("db", "")


def test_resolve_unknown_alias_raises(manager):
    with pytest.raises(AliasError, match="not found"):
        manager.resolve("ghost")


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

def test_remove_deletes_alias(manager):
    manager.add("db", "DATABASE_URL")
    manager.remove("db")
    with pytest.raises(AliasError):
        manager.resolve("db")


def test_remove_missing_alias_raises(manager):
    with pytest.raises(AliasError, match="not found"):
        manager.remove("ghost")


# ---------------------------------------------------------------------------
# list_aliases
# ---------------------------------------------------------------------------

def test_list_aliases_empty(manager):
    assert manager.list_aliases() == []


def test_list_aliases_sorted(manager):
    manager.add("z_key", "Z_VAR")
    manager.add("a_key", "A_VAR")
    names = [e["alias"] for e in manager.list_aliases()]
    assert names == ["a_key", "z_key"]


def test_list_aliases_contains_key(manager):
    manager.add("db", "DATABASE_URL")
    entries = manager.list_aliases()
    assert entries[0] == {"alias": "db", "key": "DATABASE_URL"}


# ---------------------------------------------------------------------------
# rename
# ---------------------------------------------------------------------------

def test_rename_changes_alias_name(manager):
    manager.add("db", "DATABASE_URL")
    manager.rename("db", "database")
    assert manager.resolve("database") == "DATABASE_URL"
    with pytest.raises(AliasError):
        manager.resolve("db")


def test_rename_missing_alias_raises(manager):
    with pytest.raises(AliasError, match="not found"):
        manager.rename("ghost", "new_name")


def test_rename_to_existing_alias_raises(manager):
    manager.add("db", "DATABASE_URL")
    manager.add("cache", "REDIS_URL")
    with pytest.raises(AliasError, match="already exists"):
        manager.rename("db", "cache")
