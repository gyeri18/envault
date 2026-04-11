"""Tests for envault.cli_chain."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_chain import chain_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_merge_prints_to_stdout(runner: CliRunner, tmp: Path) -> None:
    a = _write(tmp / "a.env", "FOO=bar\n")
    result = runner.invoke(chain_group, ["merge", str(a)])
    assert result.exit_code == 0
    assert "FOO=bar" in result.output


def test_merge_later_file_wins(runner: CliRunner, tmp: Path) -> None:
    a = _write(tmp / "a.env", "KEY=old\n")
    b = _write(tmp / "b.env", "KEY=new\n")
    result = runner.invoke(chain_group, ["merge", str(a), str(b)])
    assert result.exit_code == 0
    assert "KEY=new" in result.output
    assert "KEY=old" not in result.output


def test_merge_write_to_output_file(runner: CliRunner, tmp: Path) -> None:
    a = _write(tmp / "a.env", "X=1\n")
    out = tmp / "merged.env"
    result = runner.invoke(chain_group, ["merge", str(a), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "1 keys" in result.output or "X=1" in out.read_text()


def test_merge_show_sources_flag(runner: CliRunner, tmp: Path) -> None:
    a = _write(tmp / "a.env", "FOO=1\n")
    result = runner.invoke(chain_group, ["merge", "--show-sources", str(a)])
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert str(a) in result.output


def test_merge_missing_file_exits_nonzero(runner: CliRunner, tmp: Path) -> None:
    result = runner.invoke(chain_group, ["merge", str(tmp / "ghost.env")])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Error" in result.output
