"""Tests for envault.env_set."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_set import SetError, SetManager, SetResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


# ---------------------------------------------------------------------------
# SetResult
# ---------------------------------------------------------------------------

def test_set_result_changed_false_when_empty():
    r = SetResult()
    assert not r.changed


def test_set_result_summary_no_changes():
    assert SetResult().summary() == "no changes"


def test_set_result_summary_lists_operations():
    r = SetResult(added=["FOO"], updated=["BAR"])
    summary = r.summary()
    assert "added" in summary
    assert "updated" in summary


# ---------------------------------------------------------------------------
# SetManager.set
# ---------------------------------------------------------------------------

def test_set_adds_new_key(tmp_dir):
    env = tmp_dir / ".env"
    _write(env, "EXISTING=1\n")
    mgr = SetManager(env)
    result = mgr.set({"NEW_KEY": "hello"})
    assert "NEW_KEY" in result.added
    assert "NEW_KEY=hello" in env.read_text()


def test_set_updates_existing_key(tmp_dir):
    env = tmp_dir / ".env"
    _write(env, "FOO=old\n")
    mgr = SetManager(env)
    result = mgr.set({"FOO": "new"})
    assert "FOO" in result.updated
    assert "FOO=new" in env.read_text()
    assert "FOO=old" not in env.read_text()


def test_set_creates_file_when_missing(tmp_dir):
    env = tmp_dir / "new.env"
    mgr = SetManager(env)
    result = mgr.set({"KEY": "val"})
    assert env.exists()
    assert "KEY" in result.added


def test_set_raises_when_no_create_and_missing(tmp_dir):
    env = tmp_dir / "missing.env"
    mgr = SetManager(env)
    with pytest.raises(SetError, match="not found"):
        mgr.set({"KEY": "val"}, create=False)


def test_set_multiple_pairs(tmp_dir):
    env = tmp_dir / ".env"
    _write(env, "A=1\nB=2\n")
    mgr = SetManager(env)
    result = mgr.set({"A": "10", "C": "30"})
    assert "A" in result.updated
    assert "C" in result.added
    text = env.read_text()
    assert "A=10" in text
    assert "C=30" in text


def test_set_preserves_comments(tmp_dir):
    env = tmp_dir / ".env"
    _write(env, "# comment\nFOO=bar\n")
    mgr = SetManager(env)
    mgr.set({"FOO": "baz"})
    assert "# comment" in env.read_text()


# ---------------------------------------------------------------------------
# SetManager.unset
# ---------------------------------------------------------------------------

def test_unset_removes_key(tmp_dir):
    env = tmp_dir / ".env"
    _write(env, "FOO=1\nBAR=2\n")
    mgr = SetManager(env)
    removed = mgr.unset(["FOO"])
    assert removed == ["FOO"]
    assert "FOO" not in env.read_text()
    assert "BAR=2" in env.read_text()


def test_unset_missing_key_returns_empty(tmp_dir):
    env = tmp_dir / ".env"
    _write(env, "FOO=1\n")
    mgr = SetManager(env)
    removed = mgr.unset(["NONEXISTENT"])
    assert removed == []


def test_unset_raises_when_file_missing(tmp_dir):
    env = tmp_dir / "ghost.env"
    mgr = SetManager(env)
    with pytest.raises(SetError):
        mgr.unset(["FOO"])
