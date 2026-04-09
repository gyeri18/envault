"""Tests for envault.import_env.ImportManager."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.exceptions import EnvaultError, ValidationError
from envault.import_env import ImportManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_vault(tmp_path: Path) -> MagicMock:
    vault = MagicMock()
    # unlock raises by default (no existing vault)
    vault.unlock.side_effect = EnvaultError("no vault")
    return vault


@pytest.fixture()
def manager(mock_vault: MagicMock) -> ImportManager:
    return ImportManager(vault=mock_vault)


@pytest.fixture()
def dotenv_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text('DB_HOST=localhost\nDB_PORT=5432\n# comment\nSECRET="hunter2"\n')
    return p


@pytest.fixture()
def json_file(tmp_path: Path) -> Path:
    p = tmp_path / "env.json"
    p.write_text(json.dumps({"API_KEY": "abc123", "DEBUG": "true"}))
    return p


@pytest.fixture()
def shell_file(tmp_path: Path) -> Path:
    p = tmp_path / "env.sh"
    p.write_text("export APP_ENV=production\nexport PORT=8080\n")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_import_dotenv_parses_correctly(manager: ImportManager, dotenv_file: Path) -> None:
    result = manager.import_file(dotenv_file, project="myapp", fmt="dotenv")
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"
    assert result["SECRET"] == "hunter2"
    assert len(result) == 3  # comment line excluded


def test_import_json_parses_correctly(manager: ImportManager, json_file: Path) -> None:
    result = manager.import_file(json_file, project="myapp", fmt="json")
    assert result["API_KEY"] == "abc123"
    assert result["DEBUG"] == "true"


def test_import_shell_parses_correctly(manager: ImportManager, shell_file: Path) -> None:
    result = manager.import_file(shell_file, project="myapp", fmt="shell")
    assert result["APP_ENV"] == "production"
    assert result["PORT"] == "8080"


def test_import_calls_vault_lock(manager: ImportManager, dotenv_file: Path, mock_vault: MagicMock) -> None:
    manager.import_file(dotenv_file, project="proj", fmt="dotenv")
    mock_vault.lock.assert_called_once()
    call_args = mock_vault.lock.call_args
    assert call_args[0][0] == "proj"


def test_import_missing_file_raises(manager: ImportManager, tmp_path: Path) -> None:
    with pytest.raises(EnvaultError, match="not found"):
        manager.import_file(tmp_path / "ghost.env", project="x", fmt="dotenv")


def test_import_unsupported_format_raises(manager: ImportManager, dotenv_file: Path) -> None:
    with pytest.raises(ValidationError, match="Unsupported format"):
        manager.import_file(dotenv_file, project="x", fmt="xml")  # type: ignore[arg-type]


def test_import_invalid_json_raises(manager: ImportManager, tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json}")
    with pytest.raises(ValidationError, match="Invalid JSON"):
        manager.import_file(bad, project="x", fmt="json")


def test_import_merges_with_existing_vault(tmp_path: Path) -> None:
    vault = MagicMock()
    vault.unlock.return_value = {"EXISTING": "value"}
    mgr = ImportManager(vault=vault)

    src = tmp_path / ".env"
    src.write_text("NEW_KEY=new_val\n")

    result = mgr.import_file(src, project="proj", fmt="dotenv", overwrite=False)
    assert result["EXISTING"] == "value"
    assert result["NEW_KEY"] == "new_val"


def test_import_overwrite_skips_existing(tmp_path: Path) -> None:
    vault = MagicMock()
    vault.unlock.return_value = {"OLD": "data"}
    mgr = ImportManager(vault=vault)

    src = tmp_path / ".env"
    src.write_text("FRESH=yes\n")

    result = mgr.import_file(src, project="proj", fmt="dotenv", overwrite=True)
    assert "OLD" not in result
    assert result["FRESH"] == "yes"
