"""Tests for envault.env_uppercase."""
from pathlib import Path

import pytest

from envault.env_uppercase import UppercaseError, UppercaseManager


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


@pytest.fixture()
def manager() -> UppercaseManager:
    return UppercaseManager()


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------

def test_check_returns_empty_for_uppercase_keys(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "DB_HOST=localhost\nAPI_KEY=abc\n")
    assert manager.check(f) == []


def test_check_returns_lowercase_keys(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "db_host=localhost\nAPI_KEY=abc\n")
    offenders = manager.check(f)
    assert offenders == ["db_host"]


def test_check_returns_mixed_case_keys(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "DbHost=localhost\nApiKey=secret\n")
    offenders = manager.check(f)
    assert set(offenders) == {"DbHost", "ApiKey"}


def test_check_ignores_comments_and_blanks(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "# comment\n\nAPI_KEY=x\n")
    assert manager.check(f) == []


def test_check_missing_file_raises(tmp_dir, manager):
    with pytest.raises(UppercaseError):
        manager.check(tmp_dir / "nonexistent.env")


# ---------------------------------------------------------------------------
# fix()
# ---------------------------------------------------------------------------

def test_fix_converts_lowercase_keys(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "db_host=localhost\napi_key=secret\n")
    result = manager.fix(f)
    assert result.changed
    assert ("db_host", "DB_HOST") in result.converted
    assert ("api_key", "API_KEY") in result.converted


def test_fix_writes_file_in_place(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "db_host=localhost\n")
    manager.fix(f)
    content = f.read_text()
    assert "DB_HOST=localhost" in content
    assert "db_host" not in content


def test_fix_dry_run_does_not_modify_file(tmp_dir, manager):
    original = "db_host=localhost\n"
    f = _write(tmp_dir / ".env", original)
    result = manager.fix(f, dry_run=True)
    assert result.changed
    assert f.read_text() == original  # file unchanged


def test_fix_already_uppercase_not_changed(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "DB_HOST=localhost\nAPI_KEY=abc\n")
    result = manager.fix(f)
    assert not result.changed
    assert len(result.skipped) == 2


def test_fix_preserves_comments_and_blank_lines(tmp_dir, manager):
    content = "# config\n\ndb_host=localhost\n"
    f = _write(tmp_dir / ".env", content)
    manager.fix(f)
    text = f.read_text()
    assert "# config" in text
    assert "DB_HOST=localhost" in text


def test_fix_missing_file_raises(tmp_dir, manager):
    with pytest.raises(UppercaseError):
        manager.fix(tmp_dir / "missing.env")


def test_fix_summary_no_changes(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "KEY=val\n")
    result = manager.fix(f)
    assert "already uppercase" in result.summary


def test_fix_summary_lists_conversions(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "my_key=val\n")
    result = manager.fix(f)
    assert "my_key" in result.summary
    assert "MY_KEY" in result.summary
