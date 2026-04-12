"""Tests for envault.env_trim."""
from pathlib import Path

import pytest

from envault.env_trim import TrimError, TrimManager, TrimResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    p = tmp_dir / ".env"
    _write(p, "KEY1=  hello  \nKEY2=world\nKEY3=  \n")
    return p


@pytest.fixture()
def manager(env_file: Path) -> TrimManager:
    return TrimManager(env_file)


# ---------------------------------------------------------------------------
# TrimResult helpers
# ---------------------------------------------------------------------------

def test_trim_result_changed_false_when_empty():
    r = TrimResult()
    assert not r.changed


def test_trim_result_summary_no_changes():
    r = TrimResult(total=3)
    assert "No values" in r.summary()
    assert "3" in r.summary()


def test_trim_result_summary_with_changes():
    r = TrimResult(trimmed=["KEY1", "KEY3"], total=3)
    assert "2" in r.summary()
    assert "KEY1" in r.summary()
    assert "KEY3" in r.summary()


# ---------------------------------------------------------------------------
# TrimManager.trim
# ---------------------------------------------------------------------------

def test_trim_detects_values_with_whitespace(manager: TrimManager):
    result = manager.trim(dry_run=True)
    assert "KEY1" in result.trimmed
    assert "KEY3" in result.trimmed


def test_trim_does_not_flag_clean_value(manager: TrimManager):
    result = manager.trim(dry_run=True)
    assert "KEY2" not in result.trimmed


def test_trim_total_counts_all_keys(manager: TrimManager):
    result = manager.trim(dry_run=True)
    assert result.total == 3


def test_trim_dry_run_does_not_modify_file(env_file: Path, manager: TrimManager):
    original = env_file.read_text()
    manager.trim(dry_run=True)
    assert env_file.read_text() == original


def test_trim_writes_cleaned_file(env_file: Path, manager: TrimManager):
    manager.trim()
    content = env_file.read_text()
    assert "KEY1=hello" in content
    assert "KEY3=" in content
    # original whitespace gone
    assert "  hello  " not in content


def test_trim_preserves_comments(tmp_dir: Path):
    p = tmp_dir / ".env"
    _write(p, "# a comment\nKEY=  val  \n")
    m = TrimManager(p)
    m.trim()
    content = p.read_text()
    assert "# a comment" in content
    assert "KEY=val" in content


def test_trim_missing_file_raises(tmp_dir: Path):
    m = TrimManager(tmp_dir / "nonexistent.env")
    with pytest.raises(TrimError, match="not found"):
        m.trim()


def test_trim_no_changes_returns_unchanged_result(tmp_dir: Path):
    p = tmp_dir / ".env"
    _write(p, "KEY=value\nFOO=bar\n")
    m = TrimManager(p)
    result = m.trim()
    assert not result.changed
    assert result.total == 2
