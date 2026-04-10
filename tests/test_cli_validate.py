"""CLI tests for the validate command group."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_validate import validate_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_check_passes_clean_env(runner, tmp):
    env = _write(tmp / ".env", "PORT=8080\n")
    schema = _write(tmp / ".envschema", "PORT!:int\n")
    result = runner.invoke(validate_group, ["check", str(env), str(schema)])
    assert result.exit_code == 0
    assert "passed" in result.output


def test_check_exits_1_on_error(runner, tmp):
    env = _write(tmp / ".env", "PORT=abc\n")
    schema = _write(tmp / ".envschema", "PORT!:int\n")
    result = runner.invoke(validate_group, ["check", str(env), str(schema)])
    assert result.exit_code == 1
    assert "ERROR" in result.output


def test_check_shows_warnings_but_exits_0(runner, tmp):
    env = _write(tmp / ".env", "PORT=8080\n")
    schema = _write(tmp / ".envschema", "PORT!:int\nDEBUG:bool\n")
    result = runner.invoke(validate_group, ["check", str(env), str(schema)])
    assert result.exit_code == 0
    assert "WARNING" in result.output


def test_generate_schema_creates_file(runner, tmp):
    env = _write(tmp / ".env", "SECRET_KEY=abc123\nDEBUG=true\n")
    out = tmp / "generated.envschema"
    result = runner.invoke(validate_group, ["generate-schema", str(env), str(out)])
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text()
    assert "SECRET_KEY" in content
    assert "DEBUG" in content
