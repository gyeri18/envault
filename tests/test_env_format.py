"""Tests for envault.env_format."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_format import FormatError, FormatManager, FormatResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def manager() -> FormatManager:
    return FormatManager()


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_format_returns_result_type(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "KEY=value\n")
    result = manager.format(f)
    assert isinstance(result, FormatResult)


def test_format_missing_file_raises(tmp_dir, manager):
    with pytest.raises(FormatError, match="File not found"):
        manager.format(tmp_dir / "missing.env")


def test_format_unchanged_file_not_marked_changed(tmp_dir, manager):
    """A file that needs no formatting should report changed=False."""
    f = _write(tmp_dir / ".env", "KEY=value\n")
    result = manager.format(f)
    assert not result.changed


# ---------------------------------------------------------------------------
# Trailing whitespace
# ---------------------------------------------------------------------------

def test_strip_trailing_whitespace(tmp_dir):
    f = _write(tmp_dir / ".env", "KEY=value   \nOTHER=x\n")
    m = FormatManager(strip_trailing_whitespace=True)
    result = m.format(f)
    assert result.changed
    assert f.read_text().splitlines()[0] == "KEY=value"


def test_no_strip_trailing_whitespace_when_disabled(tmp_dir):
    content = "KEY=value   \n"
    f = _write(tmp_dir / ".env", content)
    m = FormatManager(strip_trailing_whitespace=False)
    m.format(f)
    assert f.read_text() == content


# ---------------------------------------------------------------------------
# Blank-line collapsing
# ---------------------------------------------------------------------------

def test_collapse_blank_lines(tmp_dir):
    f = _write(tmp_dir / ".env", "A=1\n\n\nB=2\n")
    m = FormatManager(collapse_blank_lines=True)
    result = m.format(f)
    assert result.changed
    lines = f.read_text().splitlines()
    # Only one blank line should remain between A and B
    assert lines.count("") == 1


def test_no_collapse_when_disabled(tmp_dir):
    content = "A=1\n\n\nB=2\n"
    f = _write(tmp_dir / ".env", content)
    m = FormatManager(collapse_blank_lines=False)
    m.format(f)
    assert f.read_text().splitlines().count("") == 2


# ---------------------------------------------------------------------------
# Value quoting
# ---------------------------------------------------------------------------

def test_quote_values_wraps_unquoted(tmp_dir):
    f = _write(tmp_dir / ".env", "SECRET=abc123\n")
    m = FormatManager(quote_values=True)
    result = m.format(f)
    assert result.changed
    assert 'SECRET="abc123"' in f.read_text()


def test_quote_values_leaves_already_quoted(tmp_dir):
    content = 'SECRET="already"\n'
    f = _write(tmp_dir / ".env", content)
    m = FormatManager(quote_values=True)
    result = m.format(f)
    assert not result.changed
    assert f.read_text() == content
