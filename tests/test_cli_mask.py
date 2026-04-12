"""Tests for envault.cli_mask CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_mask import mask_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DB_PASSWORD=topsecret\nAPP_NAME=myapp\nAPI_KEY=key12345\n",
        encoding="utf-8",
    )
    return p


def test_show_command_masks_sensitive(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(mask_group, ["show", str(env_file)])
    assert result.exit_code == 0
    assert "DB_PASSWORD=tops*****" in result.output
    assert "APP_NAME=myapp" in result.output


def test_show_command_reports_masked_keys(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(mask_group, ["show", str(env_file)])
    assert "DB_PASSWORD" in result.stderr or "DB_PASSWORD" in result.output


def test_show_explicit_key(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(mask_group, ["show", str(env_file), "--key", "APP_NAME", "--no-auto"])
    assert result.exit_code == 0
    assert "APP_NAME=myap*" in result.output
    assert "DB_PASSWORD=topsecret" in result.output


def test_show_custom_show_chars(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(mask_group, ["show", str(env_file), "--show-chars", "2"])
    assert result.exit_code == 0
    assert "DB_PASSWORD=to*******" in result.output


def test_list_command_shows_sensitive_keys(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(mask_group, ["list", str(env_file)])
    assert result.exit_code == 0
    assert "DB_PASSWORD" in result.output
    assert "API_KEY" in result.output


def test_list_command_no_auto_shows_none(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(mask_group, ["list", str(env_file), "--no-auto"])
    assert result.exit_code == 0
    assert "No sensitive keys detected" in result.output


def test_show_missing_file_exits_nonzero(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(mask_group, ["show", str(tmp_path / "ghost.env")])
    assert result.exit_code != 0
