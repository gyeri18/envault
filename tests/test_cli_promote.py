"""Tests for envault.cli_promote CLI commands."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_promote import promote_group
from envault.env_promote import PromoteError, PromoteResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp(tmp_path: Path):
    src = tmp_path / ".env.staging"
    dst = tmp_path / ".env.prod"
    src.write_text("FOO=bar\nBAZ=qux\n")
    dst.write_text("EXISTING=1\n")
    return tmp_path, src, dst


def test_run_promotes_keys(runner, tmp):
    _, src, dst = tmp
    result = runner.invoke(promote_group, ["run", str(src), str(dst)])
    assert result.exit_code == 0
    assert "promoted" in result.output


def test_run_dry_run_does_not_modify_destination(runner, tmp):
    _, src, dst = tmp
    original = dst.read_text()
    result = runner.invoke(promote_group, ["run", str(src), str(dst), "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert dst.read_text() == original


def test_run_overwrite_flag(runner, tmp):
    _, src, dst = tmp
    dst.write_text("FOO=old\n")
    result = runner.invoke(promote_group, ["run", str(src), str(dst), "--overwrite"])
    assert result.exit_code == 0
    assert "new" not in result.output or "overwritten" in result.output


def test_run_specific_key(runner, tmp):
    _, src, dst = tmp
    result = runner.invoke(promote_group, ["run", str(src), str(dst), "--key", "FOO"])
    assert result.exit_code == 0
    assert "FOO" in dst.read_text()
    assert "BAZ" not in dst.read_text()


def test_run_error_exits_1(runner, tmp):
    _, src, dst = tmp
    with patch("envault.cli_promote.PromoteManager.promote", side_effect=PromoteError("boom")):
        result = runner.invoke(promote_group, ["run", str(src), str(dst)])
    assert result.exit_code == 1
    assert "Error: boom" in result.output


def test_run_missing_source_exits_nonzero(runner, tmp_path: Path):
    """Invoking run with a non-existent source file should exit with a non-zero code."""
    src = tmp_path / ".env.missing"
    dst = tmp_path / ".env.prod"
    dst.write_text("EXISTING=1\n")
    result = runner.invoke(promote_group, ["run", str(src), str(dst)])
    assert result.exit_code != 0
