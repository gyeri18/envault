"""Tests for envault.env_unused."""
from pathlib import Path

import pytest

from envault.env_unused import UnusedError, UnusedManager, UnusedResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def manager() -> UnusedManager:
    return UnusedManager()


def test_scan_no_unused_keys(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    ref = _write(tmp_dir / ".env.example", "DB_HOST=\nDB_PORT=\n")
    result = manager.scan(env, ref)
    assert result.ok
    assert result.unused_keys == []


def test_scan_detects_unused_key(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "DB_HOST=localhost\nOLD_SECRET=abc\n")
    ref = _write(tmp_dir / ".env.example", "DB_HOST=\n")
    result = manager.scan(env, ref)
    assert not result.ok
    assert "OLD_SECRET" in result.unused_keys


def test_scan_multiple_unused_keys(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "A=1\nB=2\nC=3\n")
    ref = _write(tmp_dir / ".env.example", "A=\n")
    result = manager.scan(env, ref)
    assert sorted(result.unused_keys) == ["B", "C"]


def test_scan_ignores_comments(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "# comment\nACTIVE=1\n")
    ref = _write(tmp_dir / ".env.example", "ACTIVE=\n")
    result = manager.scan(env, ref)
    assert result.ok


def test_scan_ignores_blank_lines(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "\nKEY=val\n\n")
    ref = _write(tmp_dir / ".env.example", "KEY=\n")
    result = manager.scan(env, ref)
    assert result.ok


def test_scan_result_summary_no_issues(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "X=1\n")
    ref = _write(tmp_dir / ".env.example", "X=\n")
    result = manager.scan(env, ref)
    assert result.summary == "No unused keys detected."


def test_scan_result_summary_with_issues(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "X=1\nY=2\n")
    ref = _write(tmp_dir / ".env.example", "X=\n")
    result = manager.scan(env, ref)
    assert "1 unused key(s)" in result.summary
    assert "Y" in result.summary


def test_scan_missing_env_file_raises(tmp_dir: Path, manager: UnusedManager) -> None:
    ref = _write(tmp_dir / ".env.example", "X=\n")
    with pytest.raises(UnusedError, match="Env file not found"):
        manager.scan(tmp_dir / "missing.env", ref)


def test_scan_missing_reference_file_raises(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "X=1\n")
    with pytest.raises(UnusedError, match="Reference file not found"):
        manager.scan(env, tmp_dir / "missing.example")


def test_result_scanned_keys_populated(tmp_dir: Path, manager: UnusedManager) -> None:
    env = _write(tmp_dir / ".env", "A=1\nB=2\n")
    ref = _write(tmp_dir / ".env.example", "A=\nB=\n")
    result = manager.scan(env, ref)
    assert sorted(result.scanned_keys) == ["A", "B"]
