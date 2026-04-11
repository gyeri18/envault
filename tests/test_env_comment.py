"""Tests for envault.env_comment."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_comment import CommentError, CommentManager


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    return _write(
        tmp_dir / ".env",
        "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n",
    )


@pytest.fixture()
def manager(env_file: Path) -> CommentManager:
    return CommentManager(env_file)


# ---------------------------------------------------------------------------


def test_set_comment_adds_inline_comment(manager: CommentManager, env_file: Path) -> None:
    manager.set("DB_HOST", "primary database host")
    content = env_file.read_text()
    assert "DB_HOST=localhost  # primary database host" in content


def test_set_comment_replaces_existing_comment(manager: CommentManager, env_file: Path) -> None:
    manager.set("DB_HOST", "first comment")
    manager.set("DB_HOST", "second comment")
    content = env_file.read_text()
    assert "second comment" in content
    assert "first comment" not in content


def test_set_comment_missing_key_raises(manager: CommentManager) -> None:
    with pytest.raises(CommentError, match="MISSING"):
        manager.set("MISSING", "some comment")


def test_set_empty_key_raises(manager: CommentManager) -> None:
    with pytest.raises(CommentError):
        manager.set("", "comment")


def test_set_empty_comment_raises(manager: CommentManager) -> None:
    with pytest.raises(CommentError):
        manager.set("DB_HOST", "")


def test_remove_comment_strips_it(manager: CommentManager, env_file: Path) -> None:
    manager.set("DB_PORT", "port number")
    manager.remove("DB_PORT")
    content = env_file.read_text()
    assert "# port number" not in content
    assert "DB_PORT=5432" in content


def test_remove_no_existing_comment_is_noop(manager: CommentManager, env_file: Path) -> None:
    before = env_file.read_text()
    manager.remove("DB_PORT")
    after = env_file.read_text()
    assert after == before


def test_remove_missing_key_raises(manager: CommentManager) -> None:
    with pytest.raises(CommentError, match="MISSING"):
        manager.remove("MISSING")


def test_list_returns_commented_keys(manager: CommentManager) -> None:
    manager.set("DB_HOST", "host comment")
    manager.set("SECRET_KEY", "keep secret")
    entries = manager.list()
    keys = [e.key for e in entries]
    assert "DB_HOST" in keys
    assert "SECRET_KEY" in keys
    assert "DB_PORT" not in keys


def test_list_empty_when_no_comments(manager: CommentManager) -> None:
    assert manager.list() == []


def test_comment_entry_str(manager: CommentManager) -> None:
    manager.set("DB_HOST", "primary")
    entry = manager.list()[0]
    assert str(entry) == "DB_HOST: primary"


def test_missing_file_raises(tmp_dir: Path) -> None:
    m = CommentManager(tmp_dir / "nonexistent.env")
    with pytest.raises(CommentError, match="not found"):
        m.list()
