"""Tests for envault.env_sort.SortManager."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_sort import SortManager
from envault.exceptions import EnvaultError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_sort_alphabetically(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "ZEBRA=1\nAPPLE=2\nMIDDLE=3\n")
    manager = SortManager(env)
    result = manager.sort()
    lines = [l for l in result.splitlines() if l.strip()]
    keys = [l.split("=")[0] for l in lines]
    assert keys == ["APPLE", "MIDDLE", "ZEBRA"]


def test_sort_reverse(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "ALPHA=1\nGAMMA=2\nBETA=3\n")
    manager = SortManager(env)
    result = manager.sort(reverse=True)
    lines = [l for l in result.splitlines() if l.strip()]
    keys = [l.split("=")[0] for l in lines]
    assert keys == ["GAMMA", "BETA", "ALPHA"]


def test_sort_writes_file(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "Z=1\nA=2\n")
    manager = SortManager(env)
    manager.sort()
    content = env.read_text(encoding="utf-8")
    assert content.index("A=2") < content.index("Z=1")


def test_sort_dry_run_does_not_write(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    original = "Z=1\nA=2\n"
    _write(env, original)
    manager = SortManager(env)
    manager.sort(dry_run=True)
    assert env.read_text(encoding="utf-8") == original


def test_sort_by_groups(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "DB_HOST=a\nAPP_NAME=b\nDB_PORT=c\nAPP_ENV=d\n")
    manager = SortManager(env)
    result = manager.sort(groups=["APP_", "DB_"])
    lines = [l for l in result.splitlines() if l.strip()]
    keys = [l.split("=")[0] for l in lines]
    assert keys.index("APP_ENV") < keys.index("DB_HOST")
    assert keys.index("APP_NAME") < keys.index("DB_PORT")


def test_is_sorted_returns_true(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "ALPHA=1\nBETA=2\nGAMMA=3\n")
    assert SortManager(env).is_sorted() is True


def test_is_sorted_returns_false(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "GAMMA=3\nALPHA=1\n")
    assert SortManager(env).is_sorted() is False


def test_missing_file_raises(tmp_dir: Path) -> None:
    manager = SortManager(tmp_dir / "nonexistent.env")
    with pytest.raises(EnvaultError):
        manager.sort()


def test_missing_file_is_sorted_raises(tmp_dir: Path) -> None:
    manager = SortManager(tmp_dir / "nonexistent.env")
    with pytest.raises(EnvaultError):
        manager.is_sorted()
