"""Tests for envault.cli_expire."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_expire import expire_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def config_dir(tmp_path: Path) -> str:
    return str(tmp_path / ".envault")


def _future() -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat()


def _past() -> str:
    return (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()


def test_set_command_success(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(expire_group, ["set", "API_KEY", _future(), "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_set_command_invalid_date_exits_1(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(expire_group, ["set", "API_KEY", "bad-date", "--config-dir", config_dir])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_remove_command_success(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(expire_group, ["set", "API_KEY", _future(), "--config-dir", config_dir])
    result = runner.invoke(expire_group, ["remove", "API_KEY", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_missing_exits_1(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(expire_group, ["remove", "GHOST", "--config-dir", config_dir])
    assert result.exit_code == 1


def test_list_command_shows_entries(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(expire_group, ["set", "MY_KEY", _future(), "--config-dir", config_dir])
    result = runner.invoke(expire_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "MY_KEY" in result.output


def test_list_command_empty(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(expire_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No expiry" in result.output


def test_check_exits_1_when_expired(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(expire_group, ["set", "OLD", _past(), "--config-dir", config_dir])
    result = runner.invoke(expire_group, ["check", "--config-dir", config_dir])
    assert result.exit_code == 1
    assert "OLD" in result.output


def test_check_exits_0_when_none_expired(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(expire_group, ["set", "NEW", _future(), "--config-dir", config_dir])
    result = runner.invoke(expire_group, ["check", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No expired" in result.output
