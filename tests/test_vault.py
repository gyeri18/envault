"""Tests for VaultManager (envault/vault.py)."""

import pytest
from pathlib import Path

from envault.vault import VaultManager


@pytest.fixture
def tmp_vault(tmp_path):
    """Return a VaultManager backed by a temporary config directory."""
    return VaultManager(config_dir=tmp_path / ".envault")


@pytest.fixture
def sample_env(tmp_path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=secret\nDB_URL=postgres://localhost/db\n")
    return env


def test_init_project_creates_key(tmp_vault):
    key = tmp_vault.init_project("myapp")
    assert isinstance(key, bytes)
    assert len(key) == 32


def test_init_project_with_password(tmp_vault):
    key = tmp_vault.init_project("myapp", password="hunter2")
    assert isinstance(key, bytes)


def test_lock_creates_vault_file(tmp_vault, sample_env):
    tmp_vault.init_project("myapp")
    vault_path = tmp_vault.lock("myapp", sample_env)
    assert vault_path.exists()
    assert vault_path.name.endswith(".vault")


def test_lock_unlock_roundtrip(tmp_vault, sample_env):
    original = sample_env.read_text()
    tmp_vault.init_project("myapp")
    vault_path = tmp_vault.lock("myapp", sample_env)
    # Remove the original to prove unlock recreates it
    sample_env.unlink()
    env_path = tmp_vault.unlock("myapp", vault_path)
    assert env_path.read_text() == original


def test_lock_unlock_with_password(tmp_vault, sample_env):
    original = sample_env.read_text()
    vault_path = tmp_vault.lock("myapp", sample_env, password="s3cr3t")
    sample_env.unlink()
    env_path = tmp_vault.unlock("myapp", vault_path, password="s3cr3t")
    assert env_path.read_text() == original


def test_unlock_wrong_password_fails(tmp_vault, sample_env):
    tmp_vault.lock("myapp", sample_env, password="correct")
    vault_path = Path(str(sample_env) + ".vault")
    with pytest.raises(Exception):
        tmp_vault.unlock("myapp", vault_path, password="wrong")


def test_lock_missing_file_raises(tmp_vault, tmp_path):
    tmp_vault.init_project("myapp")
    with pytest.raises(FileNotFoundError):
        tmp_vault.lock("myapp", tmp_path / "nonexistent.env")


def test_resolve_key_no_project_raises(tmp_vault, sample_env):
    with pytest.raises(KeyError, match="init"):
        tmp_vault.lock("unknown_project", sample_env)
