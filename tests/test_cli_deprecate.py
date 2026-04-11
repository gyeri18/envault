"""Tests for envault.cli_deprecate CLI commands."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli_deprecate import deprecate_group


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def config_dir(tmp_path: Path) -> str:
    d = tmp_path / ".envault"
    d.mkdir()
    return str(d)


@pytest.fixture
def env_file(tmp_path: Path) -> str:
    p = tmp_path / ".env"
    p.write_text("OLD_KEY=foo\nFRESH_KEY=bar\n")
    return str(p)


def test_mark_command_success(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(
        deprecate_group,
        ["mark", "OLD_KEY", "--reason", "no longer used", "--config-dir", config_dir],
    )
    assert result.exit_code == 0
    assert "OLD_KEY" in result.output


def test_mark_command_with_replacement(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(
        deprecate_group,
        ["mark", "OLD_KEY", "--reason", "renamed", "--replacement", "NEW_KEY", "--config-dir", config_dir],
    )
    assert result.exit_code == 0
    assert "NEW_KEY" in result.output


def test_mark_duplicate_exits_nonzero(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(deprecate_group, ["mark", "K", "--reason", "r", "--config-dir", config_dir])
    result = runner.invoke(deprecate_group, ["mark", "K", "--reason", "r2", "--config-dir", config_dir])
    assert result.exit_code != 0


def test_unmark_command_success(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(deprecate_group, ["mark", "K", "--reason", "r", "--config-dir", config_dir])
    result = runner.invoke(deprecate_group, ["unmark", "K", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "K" in result.output


def test_list_shows_entries(runner: CliRunner, config_dir: str) -> None:
    runner.invoke(deprecate_group, ["mark", "K", "--reason", "old", "--config-dir", config_dir])
    result = runner.invoke(deprecate_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "K" in result.output


def test_list_empty_message(runner: CliRunner, config_dir: str) -> None:
    result = runner.invoke(deprecate_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No deprecated" in result.output


def test_check_exits_1_when_deprecated(runner: CliRunner, config_dir: str, env_file: str) -> None:
    runner.invoke(deprecate_group, ["mark", "OLD_KEY", "--reason", "gone", "--config-dir", config_dir])
    result = runner.invoke(deprecate_group, ["check", env_file, "--config-dir", config_dir])
    assert result.exit_code == 1
    assert "OLD_KEY" in result.output


def test_check_exits_0_when_clean(runner: CliRunner, config_dir: str, env_file: str) -> None:
    result = runner.invoke(deprecate_group, ["check", env_file, "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No deprecated" in result.output
