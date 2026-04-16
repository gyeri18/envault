"""Tests for envault.env_protect."""
import pytest
from pathlib import Path
from envault.env_protect import ProtectManager, ProtectError, ProtectedKeyViolation


@pytest.fixture
def manager(tmp_path):
    return ProtectManager(config_dir=tmp_path / ".envault")


def test_protect_creates_entry(manager):
    manager.protect("SECRET_KEY")
    assert manager.is_protected("SECRET_KEY")


def test_protect_with_reason(manager):
    manager.protect("DB_PASSWORD", reason="never rotate automatically")
    entries = manager.list_protected()
    assert entries[0]["reason"] == "never rotate automatically"


def test_protect_duplicate_raises(manager):
    manager.protect("API_KEY")
    with pytest.raises(ProtectError, match="already protected"):
        manager.protect("API_KEY")


def test_protect_empty_key_raises(manager):
    with pytest.raises(ProtectError, match="empty"):
        manager.protect("")


def test_unprotect_removes_entry(manager):
    manager.protect("TOKEN")
    manager.unprotect("TOKEN")
    assert not manager.is_protected("TOKEN")


def test_unprotect_missing_key_raises(manager):
    with pytest.raises(ProtectError, match="not protected"):
        manager.unprotect("MISSING")


def test_list_protected_returns_sorted(manager):
    manager.protect("Z_KEY")
    manager.protect("A_KEY")
    entries = manager.list_protected()
    assert [e["key"] for e in entries] == ["A_KEY", "Z_KEY"]


def test_check_returns_violations_for_protected_keys(manager):
    manager.protect("SECRET", reason="immutable")
    violations = manager.check(["SECRET", "SAFE"])
    assert len(violations) == 1
    assert violations[0].key == "SECRET"
    assert "immutable" in violations[0].reason


def test_check_returns_empty_when_no_violations(manager):
    manager.protect("OTHER")
    violations = manager.check(["SAFE_KEY"])
    assert violations == []


def test_violation_str():
    v = ProtectedKeyViolation("MY_KEY", "do not touch")
    assert str(v) == "MY_KEY: do not touch"


def test_is_protected_false_for_unknown(manager):
    assert not manager.is_protected("UNKNOWN")
