"""Tests for envault.env_whitelist."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_whitelist import (
    WhitelistError,
    WhitelistManager,
    WhitelistResult,
    WhitelistViolation,
)


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def manager(tmp_dir: Path) -> WhitelistManager:
    return WhitelistManager(config_dir=tmp_dir)


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# WhitelistViolation / WhitelistResult
# ---------------------------------------------------------------------------

def test_violation_str():
    v = WhitelistViolation("SECRET_KEY")
    assert "SECRET_KEY" in str(v)


def test_result_ok_when_no_violations():
    result = WhitelistResult([])
    assert result.ok is True
    assert "All keys" in result.summary()


def test_result_not_ok_when_violations():
    result = WhitelistResult([WhitelistViolation("BAD")])
    assert result.ok is False
    assert "BAD" in result.summary()


# ---------------------------------------------------------------------------
# set / get / delete
# ---------------------------------------------------------------------------

def test_set_and_get_whitelist(manager: WhitelistManager):
    manager.set_whitelist("myapp", ["DB_HOST", "DB_PORT", "API_KEY"])
    keys = manager.get_whitelist("myapp")
    assert keys == ["API_KEY", "DB_HOST", "DB_PORT"]  # sorted


def test_set_deduplicates_keys(manager: WhitelistManager):
    manager.set_whitelist("myapp", ["DB_HOST", "DB_HOST", "API_KEY"])
    keys = manager.get_whitelist("myapp")
    assert keys.count("DB_HOST") == 1


def test_set_empty_project_raises(manager: WhitelistManager):
    with pytest.raises(WhitelistError, match="empty"):
        manager.set_whitelist("", ["KEY"])


def test_set_empty_keys_raises(manager: WhitelistManager):
    with pytest.raises(WhitelistError, match="at least one"):
        manager.set_whitelist("myapp", [])


def test_get_missing_project_raises(manager: WhitelistManager):
    with pytest.raises(WhitelistError, match="No whitelist"):
        manager.get_whitelist("ghost")


def test_delete_whitelist(manager: WhitelistManager):
    manager.set_whitelist("myapp", ["KEY"])
    manager.delete_whitelist("myapp")
    with pytest.raises(WhitelistError):
        manager.get_whitelist("myapp")


def test_delete_missing_raises(manager: WhitelistManager):
    with pytest.raises(WhitelistError, match="No whitelist"):
        manager.delete_whitelist("ghost")


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

def test_check_passes_when_all_keys_allowed(manager: WhitelistManager, tmp_dir: Path):
    manager.set_whitelist("myapp", ["DB_HOST", "API_KEY"])
    env = _write(tmp_dir / ".env", "DB_HOST=localhost\nAPI_KEY=secret\n")
    result = manager.check("myapp", env)
    assert result.ok


def test_check_detects_disallowed_key(manager: WhitelistManager, tmp_dir: Path):
    manager.set_whitelist("myapp", ["DB_HOST"])
    env = _write(tmp_dir / ".env", "DB_HOST=localhost\nUNKNOWN_KEY=oops\n")
    result = manager.check("myapp", env)
    assert not result.ok
    assert any(v.key == "UNKNOWN_KEY" for v in result.violations)


def test_check_ignores_comments_and_blank_lines(manager: WhitelistManager, tmp_dir: Path):
    manager.set_whitelist("myapp", ["DB_HOST"])
    env = _write(tmp_dir / ".env", "# comment\n\nDB_HOST=localhost\n")
    result = manager.check("myapp", env)
    assert result.ok
