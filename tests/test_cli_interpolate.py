"""Tests for envault.cli_interpolate."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_interpolate import interpolate_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("ROOT=/srv\nAPP=${ROOT}/app\n")
    return f


def test_show_command_expands_values(runner, env_file):
    result = runner.invoke(interpolate_group, ["show", str(env_file)])
    assert result.exit_code == 0
    assert "APP=/srv/app" in result.output


def test_show_command_context_flag(runner, tmp_path):
    f = tmp_path / ".env"
    f.write_text("FULL=${BASE}/bin\n")
    result = runner.invoke(
        interpolate_group, ["show", str(f), "--context", "BASE=/usr"]
    )
    assert result.exit_code == 0
    assert "FULL=/usr/bin" in result.output


def test_show_command_unresolved_warns(runner, tmp_path):
    f = tmp_path / ".env"
    f.write_text("X=${GHOST}\n")
    result = runner.invoke(interpolate_group, ["show", str(f)])
    assert result.exit_code == 0
    assert "GHOST" in result.output


def test_show_strict_exits_1_on_unresolved(runner, tmp_path):
    f = tmp_path / ".env"
    f.write_text("X=${GHOST}\n")
    result = runner.invoke(interpolate_group, ["show", str(f), "--strict"])
    assert result.exit_code == 1


def test_show_strict_exits_0_when_all_resolved(runner, env_file):
    result = runner.invoke(interpolate_group, ["show", str(env_file), "--strict"])
    assert result.exit_code == 0
