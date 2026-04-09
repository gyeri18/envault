"""Tests for envault.profile and envault.cli_profile."""

from __future__ import annotations

import os
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.profile import ProfileManager, DEFAULT_PROFILE
from envault.cli_profile import profile_group
from envault.exceptions import ProfileError, VaultNotFoundError


@pytest.fixture()
def tmp_profile(tmp_path):
    env = tmp_path / ".env"
    env.write_text("APP_ENV=dev\nSECRET=abc123\n")
    mgr = ProfileManager(project_name="myapp", config_dir=str(tmp_path / "cfg"))
    return mgr, env


def test_lock_creates_vault_file(tmp_profile):
    mgr, env = tmp_profile
    vault_path = mgr.lock_profile(env_file=str(env), profile="dev")
    assert vault_path.exists()


def test_unlock_restores_content(tmp_profile, tmp_path):
    mgr, env = tmp_profile
    mgr.lock_profile(env_file=str(env), profile="dev")
    out = tmp_path / "out.env"
    mgr.unlock_profile(profile="dev", output_path=str(out))
    assert out.exists()
    content = out.read_text()
    assert "APP_ENV=dev" in content
    assert "SECRET=abc123" in content


def test_list_profiles_returns_names(tmp_profile):
    mgr, env = tmp_profile
    mgr.lock_profile(env_file=str(env), profile="dev")
    mgr.lock_profile(env_file=str(env), profile="prod")
    profiles = mgr.list_profiles()
    assert "dev" in profiles
    assert "prod" in profiles


def test_unlock_missing_profile_raises(tmp_profile):
    mgr, _ = tmp_profile
    with pytest.raises(VaultNotFoundError):
        mgr.unlock_profile(profile="nonexistent")


def test_delete_profile_removes_vault(tmp_profile):
    mgr, env = tmp_profile
    mgr.lock_profile(env_file=str(env), profile="staging")
    mgr.delete_profile("staging")
    assert "staging" not in mgr.list_profiles()


def test_delete_default_profile_raises(tmp_profile):
    mgr, _ = tmp_profile
    with pytest.raises(ProfileError):
        mgr.delete_profile(DEFAULT_PROFILE)


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_lock_and_list(runner, tmp_path):
    env = tmp_path / ".env"
    env.write_text("KEY=value\n")
    cfg = str(tmp_path / "cfg")
    result = runner.invoke(profile_group, [
        "lock", "myapp", str(env), "--profile", "dev", "--config-dir", cfg
    ])
    assert result.exit_code == 0, result.output
    assert "Locked profile 'dev'" in result.output

    result = runner.invoke(profile_group, ["list", "myapp", "--config-dir", cfg])
    assert result.exit_code == 0
    assert "dev" in result.output


def test_cli_delete_default_fails(runner, tmp_path):
    cfg = str(tmp_path / "cfg")
    result = runner.invoke(profile_group, [
        "delete", "myapp", DEFAULT_PROFILE, "--config-dir", cfg
    ])
    assert result.exit_code != 0
