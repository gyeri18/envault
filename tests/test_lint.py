"""Tests for envault.lint module."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.lint import LintManager, LintResult
from envault.exceptions import EnvaultError


@pytest.fixture
def manager() -> LintManager:
    return LintManager()


@pytest.fixture
def env_file(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _write


def test_lint_clean_file_returns_no_issues(manager, env_file):
    path = env_file("APP_NAME=myapp\nDEBUG=false\n")
    result = manager.lint(path)
    assert isinstance(result, LintResult)
    assert result.issues == []
    assert not result.has_errors


def test_lint_detects_duplicate_key(manager, env_file):
    path = env_file("FOO=1\nFOO=2\n")
    result = manager.lint(path)
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("Duplicate" in i.message for i in errors)


def test_lint_detects_lowercase_key(manager, env_file):
    path = env_file("foo_bar=value\n")
    result = manager.lint(path)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("UPPER_SNAKE_CASE" in i.message for i in warnings)


def test_lint_detects_empty_value(manager, env_file):
    path = env_file("MY_VAR=\n")
    result = manager.lint(path)
    infos = [i for i in result.issues if i.severity == "info"]
    assert any("Empty value" in i.message for i in infos)


def test_lint_warns_unquoted_sensitive_key(manager, env_file):
    path = env_file("API_SECRET=abc123\n")
    result = manager.lint(path)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("quoted" in i.message for i in warnings)


def test_lint_ignores_comments_and_blank_lines(manager, env_file):
    path = env_file("# comment\n\nAPP=prod\n")
    result = manager.lint(path)
    assert result.issues == []


def test_lint_missing_file_raises(manager, tmp_path):
    with pytest.raises(EnvaultError, match="not found"):
        manager.lint(tmp_path / "nonexistent.env")


def test_lint_invalid_line_format(manager, env_file):
    path = env_file("BADLINE\n")
    result = manager.lint(path)
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("Invalid line format" in i.message for i in errors)
    assert result.has_errors
