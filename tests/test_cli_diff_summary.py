"""Tests for envault.cli_diff_summary."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_diff_summary import diff_summary_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp(tmp_path: Path):
    return tmp_path


def _write(p: Path, content: str) -> str:
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_show_no_differences_exits_0(runner, tmp):
    base = _write(tmp / "base.env", "A=1\n")
    target = _write(tmp / "target.env", "A=1\n")
    result = runner.invoke(diff_summary_group, ["show", base, target])
    assert result.exit_code == 0
    assert "No differences" in result.output


def test_show_differences_exits_1(runner, tmp):
    base = _write(tmp / "base.env", "A=1\n")
    target = _write(tmp / "target.env", "A=1\nB=2\n")
    result = runner.invoke(diff_summary_group, ["show", base, target])
    assert result.exit_code == 1
    assert "[+] B" in result.output


def test_show_summary_counts_printed(runner, tmp):
    base = _write(tmp / "base.env", "A=1\nB=old\n")
    target = _write(tmp / "target.env", "A=1\nB=new\nC=3\n")
    result = runner.invoke(diff_summary_group, ["show", base, target])
    assert "1 added" in result.output
    assert "1 changed" in result.output


def test_show_unchanged_flag(runner, tmp):
    content = "A=1\n"
    base = _write(tmp / "base.env", content)
    target = _write(tmp / "target.env", content)
    result = runner.invoke(diff_summary_group, ["show", "--show-unchanged", base, target])
    assert "[ ] A" in result.output


def test_no_redact_flag_shows_values(runner, tmp):
    base = _write(tmp / "base.env", "SECRET=old_val\n")
    target = _write(tmp / "target.env", "SECRET=new_val\n")
    result = runner.invoke(diff_summary_group, ["show", "--no-redact", base, target])
    assert "old_val" in result.output
    assert "new_val" in result.output


def test_redact_by_default_hides_values(runner, tmp):
    base = _write(tmp / "base.env", "SECRET=old_val\n")
    target = _write(tmp / "target.env", "SECRET=new_val\n")
    result = runner.invoke(diff_summary_group, ["show", base, target])
    assert "old_val" not in result.output
    assert "new_val" not in result.output
    assert "***" in result.output
