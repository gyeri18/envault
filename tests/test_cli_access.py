"""CLI integration tests for envault access commands."""
from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli_access import access_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def config_dir(tmp_path: Path) -> str:
    return str(tmp_path)


# ---------------------------------------------------------------------------
# grant
# ---------------------------------------------------------------------------

def test_grant_command_success(runner, config_dir):
    result = runner.invoke(
        access_group, ["grant", "dev", "DB_URL", "API_KEY", "--config-dir", config_dir]
    )
    assert result.exit_code == 0
    assert "dev" in result.output
    assert "DB_URL" in result.output


def test_grant_command_empty_role_exits_1(runner, config_dir):
    result = runner.invoke(
        access_group, ["grant", "", "DB_URL", "--config-dir", config_dir]
    )
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# revoke
# ---------------------------------------------------------------------------

def test_revoke_command_success(runner, config_dir):
    runner.invoke(access_group, ["grant", "dev", "DB_URL", "API_KEY", "--config-dir", config_dir])
    result = runner.invoke(
        access_group, ["revoke", "dev", "DB_URL", "--config-dir", config_dir]
    )
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_revoke_missing_role_exits_1(runner, config_dir):
    result = runner.invoke(
        access_group, ["revoke", "ghost", "DB_URL", "--config-dir", config_dir]
    )
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

def test_check_command_allowed_exits_0(runner, config_dir):
    runner.invoke(access_group, ["grant", "qa", "SECRET", "--config-dir", config_dir])
    result = runner.invoke(
        access_group, ["check", "qa", "SECRET", "--config-dir", config_dir]
    )
    assert result.exit_code == 0
    assert "can access" in result.output


def test_check_command_denied_exits_1(runner, config_dir):
    runner.invoke(access_group, ["grant", "qa", "SECRET", "--config-dir", config_dir])
    result = runner.invoke(
        access_group, ["check", "qa", "OTHER", "--config-dir", config_dir]
    )
    assert result.exit_code == 1
    assert "cannot" in result.output


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_command_shows_roles(runner, config_dir):
    runner.invoke(access_group, ["grant", "admin", "KEY1", "--config-dir", config_dir])
    runner.invoke(access_group, ["grant", "dev", "KEY2", "--config-dir", config_dir])
    result = runner.invoke(access_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "admin" in result.output
    assert "dev" in result.output


def test_list_command_no_roles(runner, config_dir):
    result = runner.invoke(access_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No roles" in result.output


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_command_success(runner, config_dir):
    runner.invoke(access_group, ["grant", "temp", "KEY", "--config-dir", config_dir])
    result = runner.invoke(access_group, ["delete", "temp", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_missing_role_exits_1(runner, config_dir):
    result = runner.invoke(access_group, ["delete", "nobody", "--config-dir", config_dir])
    assert result.exit_code == 1
