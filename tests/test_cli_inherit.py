"""Tests for envault.cli_inherit."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_inherit import inherit_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_apply_command_inherits_keys(runner: CliRunner, tmp: Path) -> None:
    base = tmp / "base.env"
    child = tmp / "child.env"
    _write(base, "FOO=1\n")
    _write(child, "BAR=2\n")

    result = runner.invoke(inherit_group, ["apply", str(base), str(child)])

    assert result.exit_code == 0
    assert "+ FOO" in result.output
    assert "FOO=1" in child.read_text()


def test_apply_command_skips_existing(runner: CliRunner, tmp: Path) -> None:
    base = tmp / "base.env"
    child = tmp / "child.env"
    _write(base, "FOO=base\n")
    _write(child, "FOO=child\n")

    result = runner.invoke(inherit_group, ["apply", str(base), str(child)])

    assert result.exit_code == 0
    assert "skipped" in result.output
    assert "FOO=child" in child.read_text()


def test_apply_command_with_prefix(runner: CliRunner, tmp: Path) -> None:
    base = tmp / "base.env"
    child = tmp / "child.env"
    _write(base, "HOST=localhost\n")
    _write(child, "")

    result = runner.invoke(
        inherit_group, ["apply", str(base), str(child), "--prefix", "PROD_"]
    )

    assert result.exit_code == 0
    assert "+ PROD_HOST" in result.output
    assert "PROD_HOST=localhost" in child.read_text()


def test_apply_command_missing_base_exits_1(runner: CliRunner, tmp: Path) -> None:
    child = tmp / "child.env"
    _write(child, "FOO=1\n")

    result = runner.invoke(
        inherit_group, ["apply", str(tmp / "ghost.env"), str(child)]
    )

    assert result.exit_code != 0
