"""Tests for envault.env_lint_fix."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_lint_fix import LintFixError, LintFixManager, LintFixResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def test_fix_result_changed_false_when_no_fixes():
    r = LintFixResult()
    assert not r.changed
    assert r.summary() == "No fixes needed."


def test_fix_result_summary_lists_fixes():
    r = LintFixResult(fixes_applied=["removed duplicate key 'FOO'"])
    assert r.changed
    assert "1 fix(es)" in r.summary()


def test_fix_missing_file_raises(tmp_dir: Path):
    manager = LintFixManager(tmp_dir / "missing.env")
    with pytest.raises(LintFixError):
        manager.fix()


def test_fix_strips_whitespace_around_equals(tmp_dir: Path):
    f = _write(tmp_dir / ".env", "FOO = bar\nBAZ=qux\n")
    manager = LintFixManager(f)
    result = manager.fix(strip_whitespace=True, remove_duplicates=False, remove_blank_runs=False)
    content = f.read_text()
    assert "FOO=bar" in content
    assert "BAZ=qux" in content
    assert result.changed


def test_fix_removes_duplicate_keys(tmp_dir: Path):
    f = _write(tmp_dir / ".env", "FOO=1\nBAR=2\nFOO=3\n")
    manager = LintFixManager(f)
    result = manager.fix(remove_duplicates=True, strip_whitespace=False, remove_blank_runs=False)
    content = f.read_text()
    lines = [l for l in content.splitlines() if l.startswith("FOO")]
    assert len(lines) == 1
    assert "FOO=1" in content
    assert result.changed


def test_fix_collapses_multiple_blank_lines(tmp_dir: Path):
    f = _write(tmp_dir / ".env", "FOO=1\n\n\n\nBAR=2\n")
    manager = LintFixManager(f)
    result = manager.fix(remove_duplicates=False, strip_whitespace=False, remove_blank_runs=True)
    content = f.read_text()
    assert "\n\n\n" not in content
    assert result.changed


def test_fix_no_change_when_all_disabled(tmp_dir: Path):
    original = "FOO=1\nBAR=2\n"
    f = _write(tmp_dir / ".env", original)
    manager = LintFixManager(f)
    result = manager.fix(remove_duplicates=False, strip_whitespace=False, remove_blank_runs=False)
    assert not result.changed
    assert f.read_text() == original


def test_fix_preserves_comments(tmp_dir: Path):
    f = _write(tmp_dir / ".env", "# comment\nFOO=bar\n")
    manager = LintFixManager(f)
    result = manager.fix()
    content = f.read_text()
    assert "# comment" in content
    assert "FOO=bar" in content


def test_fix_file_written_only_when_changed(tmp_dir: Path):
    original = "FOO=bar\n"
    f = _write(tmp_dir / ".env", original)
    mtime_before = f.stat().st_mtime
    manager = LintFixManager(f)
    result = manager.fix(remove_duplicates=True, strip_whitespace=True, remove_blank_runs=True)
    # File content should still be valid
    assert f.read_text() == original
    assert not result.changed
