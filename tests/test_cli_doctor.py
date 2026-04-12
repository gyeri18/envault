"""CLI-level tests for the envault doctor check command."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli_doctor import doctor_group
from envault.storage import StorageManager


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def config_dir(tmp_path):
    return str(tmp_path / ".envault")


def test_check_command_error_exit_code(runner, tmp_path, config_dir):
    """Missing key should exit with code 2."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            doctor_group,
            ["check", "myproject", "--config-dir", config_dir],
        )
        assert result.exit_code == 2
        assert "ERROR" in result.output


def test_check_command_warning_exit_code(runner, tmp_path, config_dir):
    """Key present but no .env file → warning exit code 1."""
    storage = StorageManager(config_dir=config_dir)
    storage.save_project_key("proj", b"k" * 32)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            doctor_group,
            ["check", "proj", "--config-dir", config_dir],
        )
        assert result.exit_code == 1
        assert "WARNING" in result.output or "INFO" in result.output


def test_check_command_ok_exit_code(runner, tmp_path, config_dir):
    """Fully healthy project exits 0."""
    storage = StorageManager(config_dir=config_dir)
    storage.save_project_key("proj", b"k" * 32)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        env = Path(".") / ".env"
        env.write_text("A=1\n")
        vault = Path(".") / ".env.vault"
        vault.write_bytes(b"data")
        result = runner.invoke(
            doctor_group,
            ["check", "proj", "--config-dir", config_dir],
        )
        assert result.exit_code == 0
        assert "INFO" in result.output


def test_check_command_includes_project_name_in_output(runner, tmp_path, config_dir):
    """Output should mention the project name being checked."""
    storage = StorageManager(config_dir=config_dir)
    storage.save_project_key("myapp", b"k" * 32)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            doctor_group,
            ["check", "myapp", "--config-dir", config_dir],
        )
        assert "myapp" in result.output
