"""Tests for envault.env_redact."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_redact import RedactManager, RedactResult, DEFAULT_PATTERNS
from envault.exceptions import EnvaultError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    content = (
        "APP_NAME=myapp\n"
        "DB_PASSWORD=supersecret\n"
        "API_KEY=abc123\n"
        "DEBUG=true\n"
        "SECRET_TOKEN=xyz789\n"
        "# a comment\n"
        "PORT=8080\n"
    )
    return _write(tmp_dir / ".env", content)


@pytest.fixture()
def manager() -> RedactManager:
    return RedactManager()


# ---------------------------------------------------------------------------

def test_redact_returns_result_type(manager, env_file):
    result = manager.redact(env_file)
    assert isinstance(result, RedactResult)


def test_redact_masks_password(manager, env_file):
    result = manager.redact(env_file)
    assert any("DB_PASSWORD=***REDACTED***" in l for l in result.redacted_lines)


def test_redact_masks_api_key(manager, env_file):
    result = manager.redact(env_file)
    assert any("API_KEY=***REDACTED***" in l for l in result.redacted_lines)


def test_redact_masks_secret_token(manager, env_file):
    result = manager.redact(env_file)
    assert any("SECRET_TOKEN=***REDACTED***" in l for l in result.redacted_lines)


def test_redact_preserves_non_sensitive_keys(manager, env_file):
    result = manager.redact(env_file)
    assert any("APP_NAME=myapp" in l for l in result.redacted_lines)
    assert any("PORT=8080" in l for l in result.redacted_lines)


def test_redact_records_redacted_keys(manager, env_file):
    result = manager.redact(env_file)
    assert "DB_PASSWORD" in result.redacted_keys
    assert "API_KEY" in result.redacted_keys
    assert "SECRET_TOKEN" in result.redacted_keys
    assert "APP_NAME" not in result.redacted_keys


def test_redact_writes_dest_file(manager, env_file, tmp_dir):
    dest = tmp_dir / ".env.redacted"
    manager.redact(env_file, dest=dest)
    assert dest.exists()
    content = dest.read_text()
    assert "***REDACTED***" in content
    assert "supersecret" not in content


def test_redact_missing_file_raises(manager, tmp_dir):
    with pytest.raises(EnvaultError, match="File not found"):
        manager.redact(tmp_dir / "nonexistent.env")


def test_sensitive_keys_returns_original_values(manager, env_file):
    keys = manager.sensitive_keys(env_file)
    assert keys["DB_PASSWORD"] == "supersecret"
    assert keys["API_KEY"] == "abc123"
    assert "APP_NAME" not in keys


def test_custom_mask(env_file):
    m = RedactManager(mask="[hidden]")
    result = m.redact(env_file)
    assert any("[hidden]" in l for l in result.redacted_lines)


def test_custom_pattern(tmp_dir):
    env = _write(tmp_dir / ".env", "MY_CUSTOM_VAR=value\nSAFE=ok\n")
    m = RedactManager(patterns=[r"CUSTOM"])
    result = m.redact(env)
    assert any("MY_CUSTOM_VAR=***REDACTED***" in l for l in result.redacted_lines)
    assert any("SAFE=ok" in l for l in result.redacted_lines)


def test_invalid_pattern_raises():
    with pytest.raises(EnvaultError, match="Invalid redaction pattern"):
        RedactManager(patterns=["[invalid"])
