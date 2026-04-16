"""Tests for envault.cli_protect."""
import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_protect import protect_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def config_dir(tmp_path):
    return str(tmp_path / ".envault")


def test_mark_command_success(runner, config_dir):
    result, ["mark", "SECRET", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "protected" in result.output


def test_mark_command_duplicate_exits_1(runner, config_dir):
    runner.invoke(protect_group, ["mark", "SECRET", "--config-dir", config_dir])
    result = runner.invoke(protect_group, ["mark", "SECRET", "--config-dir", config_dir])
    assert result.exit_code == 1
    assert "already protected" in result.output


def test_unmark_command_success(runner, config_dir):
    runner.invoke(protect_group, ["mark", "TOKEN", "--config-dir", config_dir])
    result = runner.invoke(protect_group, ["unmark", "TOKEN", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "no longer protected" in result.output


def test_unmark_missing_exits_1(runner, config_dir):
    result = runner.invoke(protect_group, ["unmark", "GHOST", "--config-dir", config_dir])
    assert result.exit_code == 1


def test_list_command_shows_keys(runner, config_dir):
    runner.invoke(protect_group, ["mark", "DB_PASS", "--reason", "critical", "--config-dir", config_dir])
    result = runner.invoke(protect_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "DB_PASS" in result.output
    assert "critical" in result.output


def test_list_command_empty(runner, config_dir):
    result = runner.invoke(protect_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No protected" in result.output


def test_check_command_violation_exits_1(runner, config_dir):
    runner.invoke(protect_group, ["mark", "SECRET", "--config-dir", config_dir])
    result = runner.invoke(protect_group, ["check", "SECRET", "--config-dir", config_dir])
    assert result.exit_code == 1


def test_check_command_no_violation_exits_0(runner, config_dir):
    runner.invoke(protect_group, ["mark", "OTHER", "--config-dir", config_dir])
    result = runner.invoke(protect_group, ["check", "SAFE", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No violations" in result.output
