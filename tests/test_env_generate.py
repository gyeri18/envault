"""Tests for envault.env_generate."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_generate import GenerateManager, GenerateError


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_generate_creates_key(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    result = manager.generate(["SECRET_KEY"])
    assert "SECRET_KEY" in result.generated
    assert len(result.generated["SECRET_KEY"]) == 32


def test_generate_writes_to_file(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    manager.generate(["API_TOKEN"])
    content = env.read_text()
    assert "API_TOKEN=" in content


def test_generate_multiple_keys(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    result = manager.generate(["KEY_A", "KEY_B", "KEY_C"])
    assert set(result.generated.keys()) == {"KEY_A", "KEY_B", "KEY_C"}
    assert len(result.skipped) == 0


def test_generate_skips_existing_key_without_overwrite(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "EXISTING=old_value\n")
    manager = GenerateManager(env)
    result = manager.generate(["EXISTING"])
    assert "EXISTING" in result.skipped
    assert "EXISTING" not in result.generated
    assert "old_value" in env.read_text()


def test_generate_overwrites_existing_key_when_flag_set(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "EXISTING=old_value\n")
    manager = GenerateManager(env)
    result = manager.generate(["EXISTING"], overwrite=True)
    assert "EXISTING" in result.generated
    assert result.generated["EXISTING"] != "old_value"


def test_generate_custom_length(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    result = manager.generate(["SHORT"], length=16)
    assert len(result.generated["SHORT"]) == 16


def test_generate_alphanumeric_charset(tmp_dir: Path) -> None:
    import string
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    result = manager.generate(["AN_KEY"], charset="alphanumeric", length=64)
    value = result.generated["AN_KEY"]
    allowed = set(string.ascii_letters + string.digits)
    assert all(c in allowed for c in value)


def test_generate_invalid_charset_raises(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    with pytest.raises(GenerateError, match="Unknown charset"):
        manager.generate(["KEY"], charset="binary")


def test_generate_invalid_length_raises(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    with pytest.raises(GenerateError, match="Length must be between"):
        manager.generate(["KEY"], length=0)


def test_generate_invalid_key_name_raises(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    manager = GenerateManager(env)
    with pytest.raises(GenerateError, match="Invalid key name"):
        manager.generate(["123INVALID"])


def test_generate_preserves_existing_keys(tmp_dir: Path) -> None:
    env = tmp_dir / ".env"
    _write(env, "KEEP=original\n")
    manager = GenerateManager(env)
    manager.generate(["NEW_KEY"])
    content = env.read_text()
    assert "KEEP=original" in content
    assert "NEW_KEY=" in content
