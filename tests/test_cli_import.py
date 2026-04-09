"""Tests for the CLI import commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_import import import_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\nOTHER=123\n")
    return p


def _mock_manager(mapping: dict | None = None):
    """Return a patched ImportManager whose import_file returns *mapping*."""
    mapping = mapping or {"KEY": "value", "OTHER": "123"}
    mock = MagicMock()
    mock.return_value.import_file.return_value = mapping
    return mock


def test_import_file_success(runner: CliRunner, env_file: Path) -> None:
    with patch("envault.cli_import.ImportManager", _mock_manager()):
        with patch("envault.cli_import.StorageManager"), patch("envault.cli_import.VaultManager"):
            result = runner.invoke(
                import_group,
                ["file", "myapp", str(env_file)],
            )
    assert result.exit_code == 0
    assert "Imported 2 key(s)" in result.output
    assert "KEY" in result.output
    assert "OTHER" in result.output


def test_import_file_json_format(runner: CliRunner, tmp_path: Path) -> None:
    src = tmp_path / "env.json"
    src.write_text(json.dumps({"A": "1"}))
    mapping = {"A": "1"}
    with patch("envault.cli_import.ImportManager", _mock_manager(mapping)):
        with patch("envault.cli_import.StorageManager"), patch("envault.cli_import.VaultManager"):
            result = runner.invoke(
                import_group,
                ["file", "proj", str(src), "--format", "json"],
            )
    assert result.exit_code == 0
    assert "Imported 1 key(s)" in result.output


def test_import_file_with_password(runner: CliRunner, env_file: Path) -> None:
    mock_cls = _mock_manager()
    with patch("envault.cli_import.ImportManager", mock_cls):
        with patch("envault.cli_import.StorageManager"), patch("envault.cli_import.VaultManager"):
            result = runner.invoke(
                import_group,
                ["file", "proj", str(env_file), "--password", "s3cr3t"],
            )
    assert result.exit_code == 0
    _, kwargs = mock_cls.return_value.import_file.call_args
    assert kwargs.get("password") == "s3cr3t"


def test_import_file_error_shows_message(runner: CliRunner, env_file: Path) -> None:
    mock_cls = MagicMock()
    mock_cls.return_value.import_file.side_effect = Exception("something broke")
    with patch("envault.cli_import.ImportManager", mock_cls):
        with patch("envault.cli_import.StorageManager"), patch("envault.cli_import.VaultManager"):
            result = runner.invoke(
                import_group,
                ["file", "proj", str(env_file)],
            )
    assert result.exit_code != 0
    assert "something broke" in result.output
