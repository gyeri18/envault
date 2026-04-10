"""Tests for envault.env_rename.RenameManager."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envault.env_rename import RenameManager
from envault.exceptions import EnvaultError


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_vault(tmp_path: Path):
    """Return a RenameManager whose VaultManager is fully mocked."""
    vault_file = tmp_path / "test.vault"
    manager = RenameManager(vault_file, config_dir=tmp_path)

    mock_vm = MagicMock()
    manager._vault = mock_vm
    return manager, mock_vm


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_rename_moves_key(mock_vault):
    manager, vm = mock_vault
    vm.unlock.return_value = {"OLD_KEY": "secret", "OTHER": "value"}

    manager.rename("myproject", "OLD_KEY", "NEW_KEY")

    vm.lock.assert_called_once()
    _, locked_env = vm.lock.call_args[0][:2]
    assert "NEW_KEY" in locked_env
    assert "OLD_KEY" not in locked_env
    assert locked_env["NEW_KEY"] == "secret"


def test_rename_missing_key_raises(mock_vault):
    manager, vm = mock_vault
    vm.unlock.return_value = {"EXISTING": "val"}

    with pytest.raises(EnvaultError, match="not found"):
        manager.rename("myproject", "MISSING_KEY", "NEW_KEY")


def test_rename_destination_already_exists_raises(mock_vault):
    manager, vm = mock_vault
    vm.unlock.return_value = {"FOO": "1", "BAR": "2"}

    with pytest.raises(EnvaultError, match="already exists"):
        manager.rename("myproject", "FOO", "BAR")


def test_rename_keep_original(mock_vault):
    manager, vm = mock_vault
    vm.unlock.return_value = {"SOURCE": "data"}

    manager.rename("myproject", "SOURCE", "DEST", keep_original=True)

    _, locked_env = vm.lock.call_args[0][:2]
    assert "SOURCE" in locked_env
    assert "DEST" in locked_env
    assert locked_env["SOURCE"] == locked_env["DEST"] == "data"


def test_copy_is_keep_original_shorthand(mock_vault):
    manager, vm = mock_vault
    vm.unlock.return_value = {"ALPHA": "xyz"}

    manager.copy("myproject", "ALPHA", "BETA")

    _, locked_env = vm.lock.call_args[0][:2]
    assert "ALPHA" in locked_env
    assert "BETA" in locked_env


def test_rename_passes_password_to_vault(mock_vault):
    manager, vm = mock_vault
    vm.unlock.return_value = {"K": "v"}

    manager.rename("proj", "K", "K2", password="s3cr3t")

    vm.unlock.assert_called_once_with("proj", password="s3cr3t")
    vm.lock.assert_called_once()
    call_kwargs = vm.lock.call_args[1]
    assert call_kwargs.get("password") == "s3cr3t"
