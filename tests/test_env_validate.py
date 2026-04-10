"""Tests for envault.env_validate."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_validate import ValidateManager, ValidationResult
from envault.exceptions import EnvaultError


@pytest.fixture()
def tmp_dir(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def manager(tmp_dir):
    return ValidateManager(config_dir=tmp_dir)


# ── schema parsing ────────────────────────────────────────────────────

def test_load_schema_required_key(tmp_dir, manager):
    s = _write(tmp_dir / "s.envschema", "DATABASE_URL!:url\n")
    schema = manager.load_schema(s)
    assert schema["DATABASE_URL"]["required"] is True
    assert schema["DATABASE_URL"]["type"] == "url"


def test_load_schema_optional_defaults_to_str(tmp_dir, manager):
    s = _write(tmp_dir / "s.envschema", "DEBUG\n")
    schema = manager.load_schema(s)
    assert schema["DEBUG"]["required"] is False
    assert schema["DEBUG"]["type"] == "str"


def test_load_schema_invalid_line_raises(tmp_dir, manager):
    s = _write(tmp_dir / "bad.envschema", "123INVALID\n")
    with pytest.raises(EnvaultError):
        manager.load_schema(s)


# ── validation ────────────────────────────────────────────────────────

def test_validate_clean_passes(tmp_dir, manager):
    env = _write(tmp_dir / ".env", 'DATABASE_URL=https://db.example.com\nPORT=5432\n')
    schema = _write(tmp_dir / ".envschema", "DATABASE_URL!:url\nPORT!:int\n")
    result = manager.validate(env, schema)
    assert result.ok
    assert not result.issues


def test_validate_missing_required_key_is_error(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "PORT=5432\n")
    schema = _write(tmp_dir / ".envschema", "DATABASE_URL!:url\nPORT!:int\n")
    result = manager.validate(env, schema)
    assert not result.ok
    assert any(i.key == "DATABASE_URL" for i in result.errors())


def test_validate_missing_optional_key_is_warning(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "PORT=5432\n")
    schema = _write(tmp_dir / ".envschema", "PORT!:int\nDEBUG:bool\n")
    result = manager.validate(env, schema)
    assert result.ok
    assert any(i.key == "DEBUG" and i.level == "warning" for i in result.issues)


def test_validate_wrong_int_type(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "PORT=not_a_number\n")
    schema = _write(tmp_dir / ".envschema", "PORT!:int\n")
    result = manager.validate(env, schema)
    assert not result.ok


def test_validate_wrong_bool_type(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "DEBUG=maybe\n")
    schema = _write(tmp_dir / ".envschema", "DEBUG!:bool\n")
    result = manager.validate(env, schema)
    assert not result.ok


def test_validate_valid_email(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "ADMIN_EMAIL=admin@example.com\n")
    schema = _write(tmp_dir / ".envschema", "ADMIN_EMAIL!:email\n")
    result = manager.validate(env, schema)
    assert result.ok


def test_validate_invalid_email(tmp_dir, manager):
    env = _write(tmp_dir / ".env", "ADMIN_EMAIL=not-an-email\n")
    schema = _write(tmp_dir / ".envschema", "ADMIN_EMAIL!:email\n")
    result = manager.validate(env, schema)
    assert not result.ok
