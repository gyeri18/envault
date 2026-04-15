"""Tests for envault.env_interpolate."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_interpolate import InterpolateManager, InterpolateError, InterpolateResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    return _write(
        tmp_dir / ".env",
        "BASE=/opt/app\nDATA=${BASE}/data\nLOG=${DATA}/logs\n",
    )


@pytest.fixture()
def manager(env_file: Path) -> InterpolateManager:
    return InterpolateManager(env_file)


def test_interpolate_result_ok_when_no_unresolved(manager):
    result = manager.interpolate()
    assert result.ok


def test_interpolate_expands_simple_reference(manager):
    result = manager.interpolate()
    assert result.pairs["DATA"] == "/opt/app/data"


def test_interpolate_expands_chained_references(manager):
    result = manager.interpolate()
    assert result.pairs["LOG"] == "/opt/app/data/logs"


def test_interpolate_missing_reference_is_unresolved(tmp_dir):
    f = _write(tmp_dir / ".env", "X=${UNDEFINED_VAR}\n")
    result = InterpolateManager(f).interpolate()
    assert not result.ok
    assert "UNDEFINED_VAR" in result.unresolved


def test_interpolate_context_provides_external_value(tmp_dir):
    f = _write(tmp_dir / ".env", "FULL=${PREFIX}/bin\n")
    result = InterpolateManager(f).interpolate(context={"PREFIX": "/usr"})
    assert result.pairs["FULL"] == "/usr/bin"
    assert result.ok


def test_file_value_overrides_context(tmp_dir):
    """Keys defined in the file shadow the same key in context."""
    f = _write(tmp_dir / ".env", "A=file_val\nB=${A}\n")
    result = InterpolateManager(f).interpolate(context={"A": "ctx_val"})
    assert result.pairs["B"] == "file_val"


def test_missing_file_raises(tmp_dir):
    with pytest.raises(InterpolateError, match="File not found"):
        InterpolateManager(tmp_dir / "missing.env").interpolate()


def test_summary_ok(manager):
    result = manager.interpolate()
    assert "no unresolved" in result.summary()


def test_summary_with_unresolved(tmp_dir):
    f = _write(tmp_dir / ".env", "X=${GHOST}\n")
    result = InterpolateManager(f).interpolate()
    assert "GHOST" in result.summary()


def test_result_type(manager):
    result = manager.interpolate()
    assert isinstance(result, InterpolateResult)
