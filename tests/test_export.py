"""Tests for ExportManager."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envault.export import ExportManager
from envault.exceptions import ExportError


SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=hunter2\n"


@pytest.fixture()
def mock_vault(tmp_path):
    """Return a VaultManager mock whose unlock() writes a temp .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV)

    vault = MagicMock()
    vault.unlock.return_value = env_file
    return vault


@pytest.fixture()
def manager(mock_vault):
    return ExportManager(vault=mock_vault)


def test_export_dotenv_format(manager):
    result = manager.export("myproject", fmt="dotenv")
    assert "DB_HOST=localhost" in result
    assert "DB_PORT=5432" in result
    assert "SECRET=hunter2" in result


def test_export_json_format(manager):
    result = manager.export("myproject", fmt="json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"
    assert data["SECRET"] == "hunter2"


def test_export_shell_format(manager):
    result = manager.export("myproject", fmt="shell")
    assert "export DB_HOST=localhost" in result
    assert "export SECRET=hunter2" in result


def test_export_unsupported_format_raises(manager):
    with pytest.raises(ExportError, match="Unsupported format"):
        manager.export("myproject", fmt="xml")


def test_export_writes_to_output_file(manager, tmp_path):
    out = tmp_path / "output.json"
    manager.export("myproject", fmt="json", output_path=out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["DB_HOST"] == "localhost"


def test_export_passes_password_to_vault(mock_vault, manager):
    manager.export("myproject", fmt="dotenv", password="s3cr3t")
    mock_vault.unlock.assert_called_once_with("myproject", password="s3cr3t")


def test_parse_env_skips_comments_and_blanks(manager, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\nFOO=bar\n")
    mock_vault = MagicMock()
    mock_vault.unlock.return_value = env_file
    mgr = ExportManager(vault=mock_vault)
    result = mgr.export("proj", fmt="json")
    data = json.loads(result)
    assert "# comment" not in data
    assert data["FOO"] == "bar"
