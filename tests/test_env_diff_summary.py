"""Tests for envault.env_diff_summary."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_diff_summary import DiffSummaryManager, SummaryLine


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def manager() -> DiffSummaryManager:
    return DiffSummaryManager(redact=False)


def test_summary_line_str_added():
    line = SummaryLine("added", "FOO", new_value="bar")
    assert str(line) == "[+] FOO=bar"


def test_summary_line_str_removed():
    line = SummaryLine("removed", "FOO", old_value="bar")
    assert str(line) == "[-] FOO=bar"


def test_summary_line_str_changed():
    line = SummaryLine("changed", "FOO", old_value="old", new_value="new")
    assert "[~]" in str(line)
    assert "old" in str(line)
    assert "new" in str(line)


def test_summarise_detects_added_key(tmp_dir, manager):
    base = _write(tmp_dir / "base.env", "A=1\n")
    target = _write(tmp_dir / "target.env", "A=1\nB=2\n")
    summary = manager.summarise(base, target)
    assert len(summary.added) == 1
    assert summary.added[0].key == "B"


def test_summarise_detects_removed_key(tmp_dir, manager):
    base = _write(tmp_dir / "base.env", "A=1\nB=2\n")
    target = _write(tmp_dir / "target.env", "A=1\n")
    summary = manager.summarise(base, target)
    assert len(summary.removed) == 1
    assert summary.removed[0].key == "B"


def test_summarise_detects_changed_key(tmp_dir, manager):
    base = _write(tmp_dir / "base.env", "A=old\n")
    target = _write(tmp_dir / "target.env", "A=new\n")
    summary = manager.summarise(base, target)
    assert len(summary.changed) == 1
    assert summary.changed[0].old_value == "old"
    assert summary.changed[0].new_value == "new"


def test_summarise_identical_files_no_differences(tmp_dir, manager):
    content = "A=1\nB=2\n"
    base = _write(tmp_dir / "base.env", content)
    target = _write(tmp_dir / "target.env", content)
    summary = manager.summarise(base, target)
    assert not summary.has_differences()
    assert len(summary.unchanged) == 2


def test_redact_hides_values(tmp_dir):
    mgr = DiffSummaryManager(redact=True)
    base = _write(tmp_dir / "base.env", "SECRET=hunter2\n")
    target = _write(tmp_dir / "target.env", "SECRET=new_secret\n")
    summary = mgr.summarise(base, target)
    for line in summary.lines:
        if line.old_value:
            assert line.old_value == "***"
        if line.new_value:
            assert line.new_value == "***"


def test_render_excludes_unchanged_by_default(tmp_dir, manager):
    base = _write(tmp_dir / "base.env", "A=1\nB=2\n")
    target = _write(tmp_dir / "target.env", "A=1\nB=3\n")
    summary = manager.summarise(base, target)
    rendered = summary.render(show_unchanged=False)
    assert "[ ]" not in rendered
    assert "[~]" in rendered


def test_render_includes_unchanged_when_requested(tmp_dir, manager):
    base = _write(tmp_dir / "base.env", "A=1\nB=2\n")
    target = _write(tmp_dir / "target.env", "A=1\nB=3\n")
    summary = manager.summarise(base, target)
    rendered = summary.render(show_unchanged=True)
    assert "[ ]" in rendered


def test_comments_and_blank_lines_ignored(tmp_dir, manager):
    base = _write(tmp_dir / "base.env", "# comment\n\nA=1\n")
    target = _write(tmp_dir / "target.env", "A=1\n")
    summary = manager.summarise(base, target)
    assert not summary.has_differences()
