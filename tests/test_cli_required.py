"""Tests for envault.cli_required CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_required import required_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def test_set_command_success(runner, tmp):
    result = runner.invoke(
        required_group,
        ["set", "myproj", "DB_URL", "SECRET_KEY", "--config-dir", str(tmp)],
    )
    assert result.exit_code == 0
    assert "2 required key" in result.output


def test_list_command_shows_keys(runner, tmp):
    runner.invoke(
        required_group,
        ["set", "myproj", "DB_URL", "SECRET_KEY", "--config-dir", str(tmp)],
    )
    result = runner.invoke(
        required_group, ["list", "myproj", "--config-dir", str(tmp)]
    )
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "SECRET_KEY" in result.output


def test_list_command_no_keys_defined(runner, tmp):
    result = runner.invoke(
        required_group, ["list", "unknown", "--config-dir", str(tmp)]
    )
    assert result.exit_code == 0
    assert "No required keys" in result.output


def test_check_command_passes(runner, tmp):
    env = _write(tmp / ".env", "DB_URL=postgres://localhost\nSECRET_KEY=abc\n")
    runner.invoke(
        required_group,
        ["set", "p", "DB_URL", "SECRET_KEY", "--config-dir", str(tmp)],
    )
    result = runner.invoke(
        required_group, ["check", "p", str(env), "--config-dir", str(tmp)]
    )
    assert result.exit_code == 0
    assert "Missing : 0" in result.output


def test_check_command_exits_1_on_missing(runner, tmp):
    env = _write(tmp / ".env", "DB_URL=postgres://localhost\n")
    runner.invoke(
        required_group,
        ["set", "p", "DB_URL", "SECRET_KEY", "--config-dir", str(tmp)],
    )
    result = runner.invoke(
        required_group, ["check", "p", str(env), "--config-dir", str(tmp)]
    )
    assert result.exit_code == 1
    assert "SECRET_KEY" in result.output


def test_remove_command_success(runner, tmp):
    runner.invoke(
        required_group,
        ["set", "p", "KEY", "--config-dir", str(tmp)],
    )
    result = runner.invoke(
        required_group, ["remove", "p", "--config-dir", str(tmp)]
    )
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_command_nonexistent(runner, tmp):
    result = runner.invoke(
        required_group, ["remove", "ghost", "--config-dir", str(tmp)]
    )
    assert result.exit_code == 0
    assert "No required-keys definition found" in result.output
