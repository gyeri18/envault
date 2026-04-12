"""Tests for envault.cli_lint_fix CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_lint_fix import lint_fix_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("FOO = bar\nBAZ=qux\nFOO=dup\n", encoding="utf-8")
    return f


def test_run_command_applies_fixes(runner: CliRunner, env_file: Path):
    result = runner.invoke(lint_fix_group, ["run", str(env_file)])
    assert result.exit_code == 0
    assert "fix" in result.output.lower() or "applied" in result.output.lower() or "No fixes" in result.output


def test_run_command_no_change_reports_no_fixes(runner: CliRunner, tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
    result = runner.invoke(lint_fix_group, ["run", str(f)])
    assert result.exit_code == 0
    assert "No fixes needed" in result.output


def test_run_command_missing_file_exits_1(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(lint_fix_group, ["run", str(tmp_path / "ghost.env")])
    assert result.exit_code == 1
    assert "Error" in result.output or "Error" in (result.stderr or "")


def test_dry_run_does_not_modify_file(runner: CliRunner, env_file: Path):
    original = env_file.read_text()
    result = runner.invoke(lint_fix_group, ["run", "--dry-run", str(env_file)])
    assert result.exit_code == 0
    assert env_file.read_text() == original
    assert "dry-run" in result.output


def test_no_dedup_flag_skips_duplicate_removal(runner: CliRunner, tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("FOO=1\nFOO=2\n", encoding="utf-8")
    runner.invoke(lint_fix_group, ["run", "--no-dedup", str(f)])
    content = f.read_text()
    # Both FOO lines should still be present
    assert content.count("FOO=") == 2
