"""Tests for envault.cli_group CLI commands."""
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli_group import group_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def config_dir(tmp_path: Path) -> str:
    return str(tmp_path / ".envault")


def test_create_command_success(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(
        group_group, ["create", "db", "DB_HOST", "DB_PORT", "--config-dir", config_dir]
    )
    assert result.exit_code == 0
    assert "created" in result.output


def test_create_command_duplicate_exits_1(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(group_group, ["create", "db", "A", "--config-dir", config_dir])
    result = runner.invoke(group_group, ["create", "db", "B", "--config-dir", config_dir])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_list_command_shows_groups(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(group_group, ["create", "web", "HOST", "--config-dir", config_dir])
    result = runner.invoke(group_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "web" in result.output


def test_list_command_empty(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(group_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No groups" in result.output


def test_show_command_lists_keys(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(group_group, ["create", "db", "DB_HOST", "DB_PORT", "--config-dir", config_dir])
    result = runner.invoke(group_group, ["show", "db", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output


def test_show_missing_group_exits_1(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(group_group, ["show", "ghost", "--config-dir", config_dir])
    assert result.exit_code == 1


def test_delete_command_success(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(group_group, ["create", "grp", "A", "--config-dir", config_dir])
    result = runner.invoke(group_group, ["delete", "grp", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_add_key_command(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(group_group, ["create", "grp", "A", "--config-dir", config_dir])
    result = runner.invoke(group_group, ["add-key", "grp", "B", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "added" in result.output


def test_remove_key_command(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(group_group, ["create", "grp", "A", "B", "--config-dir", config_dir])
    result = runner.invoke(group_group, ["remove-key", "grp", "A", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "removed" in result.output
