"""Tests for envault.template.TemplateManager."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envault.template import TemplateManager
from envault.exceptions import EnvaultError


SAMPLE_ENV = """# Database config
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=supersecret

# App settings
SECRET_KEY=abc123
DEBUG=true
"""


@pytest.fixture()
def mock_vault(tmp_path: Path):
    vault = MagicMock()
    vault.unlock.return_value = SAMPLE_ENV
    return vault


@pytest.fixture()
def manager(mock_vault):
    return TemplateManager(vault=mock_vault)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(SAMPLE_ENV, encoding="utf-8")
    return p


def test_generate_creates_template_file(manager, env_file, tmp_path):
    out = manager.generate(env_file, project="default")
    assert out.exists()
    assert out.suffix == ".template"


def test_generate_redacts_values(manager, env_file):
    out = manager.generate(env_file, project="default")
    content = out.read_text(encoding="utf-8")
    assert "<REDACTED>" in content
    assert "supersecret" not in content
    assert "abc123" not in content


def test_generate_preserves_comments_and_blanks(manager, env_file):
    out = manager.generate(env_file, project="default")
    content = out.read_text(encoding="utf-8")
    assert "# Database config" in content
    assert "# App settings" in content


def test_generate_preserves_keys(manager, env_file):
    out = manager.generate(env_file, project="default")
    content = out.read_text(encoding="utf-8")
    for key in ("DB_HOST", "DB_PORT", "DB_PASSWORD", "SECRET_KEY", "DEBUG"):
        assert key in content


def test_generate_custom_output_path(manager, env_file, tmp_path):
    custom_out = tmp_path / "custom.template"
    out = manager.generate(env_file, output_path=custom_out, project="default")
    assert out == custom_out
    assert custom_out.exists()


def test_apply_fills_values(manager, env_file, tmp_path):
    template_path = manager.generate(env_file, project="default")
    output = tmp_path / ".env.filled"
    values = {
        "DB_HOST": "prod-host",
        "DB_PORT": "5433",
        "DB_PASSWORD": "newpassword",
        "SECRET_KEY": "xyz789",
        "DEBUG": "false",
    }
    result = manager.apply(template_path, values, output)
    content = result.read_text(encoding="utf-8")
    assert "DB_HOST=prod-host" in content
    assert "DB_PASSWORD=newpassword" in content
    assert "<REDACTED>" not in content


def test_apply_missing_template_raises(manager, tmp_path):
    with pytest.raises(EnvaultError, match="Template file not found"):
        manager.apply(tmp_path / "nonexistent.template", {}, tmp_path / "out.env")
