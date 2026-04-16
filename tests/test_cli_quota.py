"""Tests for envault.cli_quota."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from envault.cli_quota import quota_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def config_dir(tmp_path: Path) -> Path:
    d = tmp_path / "cfg"
    d.mkdir()
    return d


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("A=1\nB=2\nC=3\n")
    return p


def test_set_command_success(runner: CliRunner, config_dir: Path) -> None:
    result = runner.invoke(quota_group, ["set", "proj", "10", "--config-dir", str(config_dir)])
    assert result.exit_code == 0
    assert "10" in result.output


def test_set_command_invalid_limit_exits_1(runner: CliRunner, config_dir: Path) -> None:
    result = runner.invoke(quota_group, ["set", "proj", "0", "--config-dir", str(config_dir)])
    assert result.exit_code == 1


def test_list_command_empty(runner: CliRunner, config_dir: Path) -> None:
    result = runner.invoke(quota_group, ["list", "--config-dir", str(config_dir)])
    assert result.exit_code == 0
    assert "No quotas" in result.output


def test_list_command_shows_quotas(runner: CliRunner, config_dir: Path) -> None:
    runner.invoke(quota_group, ["set", "alpha", "5", "--config-dir", str(config_dir)])
    result = runner.invoke(quota_group, ["list", "--config-dir", str(config_dir)])
    assert "alpha" in result.output
    assert "5" in result.output


def test_remove_command_success(runner: CliRunner, config_dir: Path) -> None:
    runner.invoke(quota_group, ["set", "proj", "3", "--config-dir", str(config_dir)])
    result = runner.invoke(quota_group, ["remove", "proj", "--config-dir", str(config_dir)])
    assert result.exit_code == 0


def test_remove_command_missing_exits_1(runner: CliRunner, config_dir: Path) -> None:
    result = runner.invoke(quota_group, ["remove", "ghost", "--config-dir", str(config_dir)])
    assert result.exit_code == 1


def test_check_command_within_quota(runner: CliRunner, config_dir: Path, env_file: Path) -> None:
    runner.invoke(quota_group, ["set", "proj", "10", "--config-dir", str(config_dir)])
    result = runner.invoke(quota_group, ["check", "proj", str(env_file), "--config-dir", str(config_dir)])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_check_command_exceeds_quota_exits_1(runner: CliRunner, config_dir: Path, env_file: Path) -> None:
    runner.invoke(quota_group, ["set", "proj", "2", "--config-dir", str(config_dir)])
    result = runner.invoke(quota_group, ["check", "proj", str(env_file), "--config-dir", str(config_dir)])
    assert result.exit_code == 1
