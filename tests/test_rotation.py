"""Tests for envault.rotation.KeyRotationManager."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envault.rotation import KeyRotationManager
from envault.storage import StorageManager
from envault.crypto import CryptoManager
from envault.exceptions import KeyNotFoundError, VaultFileNotFoundError, RotationError


@pytest.fixture()
def tmp_vault(tmp_path: Path):
    """Return a (StorageManager, vault_path, plaintext) triple."""
    storage = StorageManager(config_dir=str(tmp_path / ".envault"))
    crypto = CryptoManager()
    key = crypto.generate_key()
    storage.save_project_key("myapp", key)

    plaintext = b"SECRET=hunter2\nDB_URL=postgres://localhost/dev"
    ciphertext = crypto.encrypt(plaintext, key)
    vault_file = tmp_path / "myapp.vault"
    vault_file.write_bytes(ciphertext)

    return storage, vault_file, plaintext


def test_rotate_produces_new_key(tmp_vault):
    storage, vault_file, plaintext = tmp_vault
    old_key = storage.get_project_key("myapp")

    mgr = KeyRotationManager(storage=storage)
    new_key = mgr.rotate("myapp", vault_file)

    assert new_key != old_key
    assert storage.get_project_key("myapp") == new_key


def test_rotated_vault_decrypts_correctly(tmp_vault):
    storage, vault_file, plaintext = tmp_vault
    mgr = KeyRotationManager(storage=storage)
    new_key = mgr.rotate("myapp", vault_file)

    crypto = CryptoManager()
    recovered = crypto.decrypt(vault_file.read_bytes(), new_key)
    assert recovered == plaintext


def test_rotate_with_password(tmp_vault):
    storage, vault_file, _ = tmp_vault
    mgr = KeyRotationManager(storage=storage)
    new_key = mgr.rotate("myapp", vault_file, password="s3cr3t!")

    crypto = CryptoManager()
    expected_key = crypto.derive_key_from_password("s3cr3t!")
    assert new_key == expected_key


def test_rotate_missing_project_key(tmp_path):
    storage = StorageManager(config_dir=str(tmp_path / ".envault"))
    mgr = KeyRotationManager(storage=storage)

    with pytest.raises(KeyNotFoundError):
        mgr.rotate("ghost", tmp_path / "ghost.vault")


def test_rotate_missing_vault_file(tmp_vault):
    storage, vault_file, _ = tmp_vault
    mgr = KeyRotationManager(storage=storage)

    with pytest.raises(VaultFileNotFoundError):
        mgr.rotate("myapp", vault_file.parent / "nonexistent.vault")


def test_rotate_records_audit_event(tmp_vault):
    storage, vault_file, _ = tmp_vault
    audit = MagicMock()
    mgr = KeyRotationManager(storage=storage, audit=audit)
    mgr.rotate("myapp", vault_file)

    audit.record.assert_called_once()
    call_kwargs = audit.record.call_args.kwargs
    assert call_kwargs["action"] == "rotate"
    assert call_kwargs["project"] == "myapp"
