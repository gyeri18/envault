"""Tests for envault.env_type_check."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_type_check import (
    TypeCheckManager,
    TypeCheckError,
    TypeViolation,
    TypeCheckResult,
)


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
        "PORT=8080\nDEBUG=true\nSCORE=3.14\nEMAIL=user@example.com\nSITE=https://example.com\nNAME=Alice\n",
    )


@pytest.fixture()
def manager(tmp_dir: Path) -> TypeCheckManager:
    return TypeCheckManager(config_dir=tmp_dir)


def test_check_all_valid(env_file: Path, manager: TypeCheckManager) -> None:
    schema = {"PORT": "int", "DEBUG": "bool", "SCORE": "float", "EMAIL": "email", "SITE": "url", "NAME": "str"}
    result = manager.check(env_file, schema)
    assert result.ok
    assert result.violations == []


def test_check_detects_invalid_int(tmp_dir: Path, manager: TypeCheckManager) -> None:
    f = _write(tmp_dir / "a.env", "PORT=not_a_number\n")
    result = manager.check(f, {"PORT": "int"})
    assert not result.ok
    assert len(result.violations) == 1
    assert result.violations[0].key == "PORT"
    assert result.violations[0].expected == "int"


def test_check_detects_invalid_bool(tmp_dir: Path, manager: TypeCheckManager) -> None:
    f = _write(tmp_dir / "b.env", "DEBUG=maybe\n")
    result = manager.check(f, {"DEBUG": "bool"})
    assert not result.ok


def test_check_valid_bool_variants(tmp_dir: Path, manager: TypeCheckManager) -> None:
    for val in ("true", "false", "1", "0", "yes", "no", "on", "off"):
        f = _write(tmp_dir / f"bool_{val}.env", f"FLAG={val}\n")
        result = manager.check(f, {"FLAG": "bool"})
        assert result.ok, f"Expected {val!r} to be valid bool"


def test_check_invalid_url(tmp_dir: Path, manager: TypeCheckManager) -> None:
    f = _write(tmp_dir / "c.env", "SITE=not-a-url\n")
    result = manager.check(f, {"SITE": "url"})
    assert not result.ok


def test_check_invalid_email(tmp_dir: Path, manager: TypeCheckManager) -> None:
    f = _write(tmp_dir / "d.env", "EMAIL=bademail\n")
    result = manager.check(f, {"EMAIL": "email"})
    assert not result.ok


def test_check_missing_key_in_file_is_skipped(tmp_dir: Path, manager: TypeCheckManager) -> None:
    f = _write(tmp_dir / "e.env", "NAME=Alice\n")
    result = manager.check(f, {"PORT": "int"})
    assert result.ok


def test_check_missing_file_raises(tmp_dir: Path, manager: TypeCheckManager) -> None:
    with pytest.raises(TypeCheckError, match="File not found"):
        manager.check(tmp_dir / "missing.env", {"X": "str"})


def test_unsupported_type_in_schema_raises(env_file: Path, manager: TypeCheckManager) -> None:
    with pytest.raises(TypeCheckError, match="Unsupported type"):
        manager.check(env_file, {"NAME": "uuid"})


def test_summary_ok(env_file: Path, manager: TypeCheckManager) -> None:
    result = manager.check(env_file, {"NAME": "str"})
    assert "All values" in result.summary()


def test_summary_with_violations(tmp_dir: Path, manager: TypeCheckManager) -> None:
    f = _write(tmp_dir / "f.env", "PORT=abc\n")
    result = manager.check(f, {"PORT": "int"})
    summary = result.summary()
    assert "violation" in summary
    assert "PORT" in summary


def test_violation_str(tmp_dir: Path, manager: TypeCheckManager) -> None:
    v = TypeViolation(key="PORT", expected="int", actual_value="abc")
    assert "PORT" in str(v)
    assert "int" in str(v)
    assert "abc" in str(v)
