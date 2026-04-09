"""Integration tests for the Click CLI (envault/cli.py)."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path) -> Path:
    p = tmp_path / ".env"
    p.write_text("SECRET=abc123\n")
    return p


def _config_dir_args(tmp_path: Path):
    """We monkey-patch via env var in a real scenario; here we test end-to-end."""
    return []


def test_init_command(runner, tmp_path):
    result = runner.invoke(cli, ["init", "testproject"])
    assert result.exit_code == 0
    assert "initialised" in result.output


def test_init_with_password(runner):
    result = runner.invoke(cli, ["init", "testproject", "--password", "mypass"])
    assert result.exit_code == 0


def test_lock_command(runner, env_file):
    runner.invoke(cli, ["init", "testproject"])
    result = runner.invoke(cli, ["lock", "testproject", str(env_file)])
    assert result.exit_code == 0
    assert "Locked" in result.output
    assert Path(str(env_file) + ".vault").exists()


def test_unlock_command(runner, env_file):
    original = env_file.read_text()
    runner.invoke(cli, ["init", "testproject"])
    runner.invoke(cli, ["lock", "testproject", str(env_file)])
    vault_file = Path(str(env_file) + ".vault")
    env_file.unlink()
    result = runner.invoke(cli, ["unlock", "testproject", str(vault_file)])
    assert result.exit_code == 0
    assert "Unlocked" in result.output
    assert env_file.read_text() == original


def test_lock_nonexistent_file(runner, tmp_path):
    runner.invoke(cli, ["init", "testproject"])
    result = runner.invoke(cli, ["lock", "testproject", str(tmp_path / "missing.env")])
    assert result.exit_code != 0
