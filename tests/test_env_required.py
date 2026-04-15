"""Tests for envault.env_required."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_required import MissingKeyResult, RequiredError, RequiredManager


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def manager(tmp_dir: Path) -> RequiredManager:
    return RequiredManager(config_dir=tmp_dir)


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


# --- MissingKeyResult ---

def test_result_ok_when_no_missing():
    r = MissingKeyResult(missing=[], present=["A", "B"])
    assert r.ok is True


def test_result_not_ok_when_missing():
    r = MissingKeyResult(missing=["SECRET"], present=["A"])
    assert r.ok is False


def test_result_summary_lists_missing():
    r = MissingKeyResult(missing=["SECRET"], present=["A"])
    summary = r.summary()
    assert "SECRET" in summary
    assert "Missing : 1" in summary


# --- set / get required ---

def test_set_required_stores_sorted_unique(manager):
    manager.set_required("proj", ["B", "A", "A"])
    keys = manager.get_required("proj")
    assert keys == ["A", "B"]


def test_get_required_returns_empty_for_unknown(manager):
    assert manager.get_required("no_such_project") == []


def test_set_required_empty_project_raises(manager):
    with pytest.raises(RequiredError):
        manager.set_required("", ["KEY"])


def test_set_required_empty_keys_raises(manager):
    with pytest.raises(RequiredError):
        manager.set_required("proj", [])


# --- check ---

def test_check_all_present(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "A=1\nB=2\n")
    manager.set_required("proj", ["A", "B"])
    result = manager.check("proj", env)
    assert result.ok
    assert set(result.present) == {"A", "B"}
    assert result.missing == []


def test_check_detects_missing(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "A=1\n")
    manager.set_required("proj", ["A", "SECRET"])
    result = manager.check("proj", env)
    assert not result.ok
    assert "SECRET" in result.missing


def test_check_ignores_comments(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "# SECRET=hidden\nA=1\n")
    manager.set_required("proj", ["SECRET"])
    result = manager.check("proj", env)
    assert "SECRET" in result.missing


def test_check_missing_file_raises(tmp_dir, manager):
    manager.set_required("proj", ["A"])
    with pytest.raises(RequiredError):
        manager.check("proj", tmp_dir / "nonexistent.env")


# --- remove ---

def test_remove_existing_returns_true(manager):
    manager.set_required("proj", ["A"])
    assert manager.remove_required("proj") is True
    assert manager.get_required("proj") == []


def test_remove_nonexistent_returns_false(manager):
    assert manager.remove_required("ghost") is False
