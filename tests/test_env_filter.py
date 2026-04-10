"""Tests for envault.env_filter.FilterManager."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_filter import FilterManager
from envault.exceptions import EnvaultError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    return _write(
        tmp_dir / ".env",
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_PASSWORD=secret\n"
        "AWS_ACCESS_KEY=AKIA123\n"
        "AWS_SECRET_KEY=abc/xyz\n"
        "APP_DEBUG=true\n"
        "APP_ENV=production\n"
        "# comment line\n"
        "EMPTY=\n",
    )


@pytest.fixture()
def manager(env_file: Path) -> FilterManager:
    return FilterManager(env_file)


# ---------------------------------------------------------------------------
# prefix
# ---------------------------------------------------------------------------

def test_filter_by_prefix_returns_matching_keys(manager: FilterManager) -> None:
    result = manager.filter(prefix="DB_")
    assert set(result.keys()) == {"DB_HOST", "DB_PORT", "DB_PASSWORD"}


def test_filter_by_prefix_values_correct(manager: FilterManager) -> None:
    result = manager.filter(prefix="AWS_")
    assert result["AWS_ACCESS_KEY"] == "AKIA123"
    assert result["AWS_SECRET_KEY"] == "abc/xyz"


# ---------------------------------------------------------------------------
# suffix
# ---------------------------------------------------------------------------

def test_filter_by_suffix(manager: FilterManager) -> None:
    result = manager.filter(suffix="_KEY")
    assert set(result.keys()) == {"AWS_ACCESS_KEY", "AWS_SECRET_KEY"}


# ---------------------------------------------------------------------------
# glob pattern
# ---------------------------------------------------------------------------

def test_filter_by_glob_pattern(manager: FilterManager) -> None:
    result = manager.filter(pattern="APP_*")
    assert set(result.keys()) == {"APP_DEBUG", "APP_ENV"}


def test_filter_by_glob_no_match_returns_empty(manager: FilterManager) -> None:
    result = manager.filter(pattern="MISSING_*")
    assert result == {}


# ---------------------------------------------------------------------------
# invert
# ---------------------------------------------------------------------------

def test_filter_invert_excludes_matching_keys(manager: FilterManager) -> None:
    result = manager.filter(prefix="DB_", invert=True)
    assert "DB_HOST" not in result
    assert "AWS_ACCESS_KEY" in result
    assert "APP_DEBUG" in result


# ---------------------------------------------------------------------------
# list_keys
# ---------------------------------------------------------------------------

def test_list_keys_returns_only_names(manager: FilterManager) -> None:
    keys = manager.list_keys(prefix="DB_")
    assert isinstance(keys, list)
    assert "DB_HOST" in keys
    for k in keys:
        assert k.startswith("DB_")


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_missing_file_raises(tmp_dir: Path) -> None:
    mgr = FilterManager(tmp_dir / "nonexistent.env")
    with pytest.raises(EnvaultError, match="not found"):
        mgr.filter(prefix="X")


def test_no_criterion_raises(manager: FilterManager) -> None:
    with pytest.raises(EnvaultError, match="at least one"):
        manager.filter()


def test_multiple_criteria_raises(manager: FilterManager) -> None:
    with pytest.raises(EnvaultError, match="Only one"):
        manager.filter(prefix="DB_", suffix="_KEY")
