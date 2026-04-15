"""Tests for envault.env_inherit."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_inherit import InheritError, InheritManager


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_inherit_adds_missing_keys(tmp_dir: Path) -> None:
    base = tmp_dir / "base.env"
    child = tmp_dir / "child.env"
    _write(base, "FOO=1\nBAR=2\n")
    _write(child, "BAZ=3\n")

    manager = InheritManager(base, child)
    result = manager.apply()

    assert "FOO" in result.added
    assert "BAR" in result.added
    assert result.changed is True
    assert "FOO=1" in child.read_text()
    assert "BAR=2" in child.read_text()


def test_inherit_skips_existing_keys_by_default(tmp_dir: Path) -> None:
    base = tmp_dir / "base.env"
    child = tmp_dir / "child.env"
    _write(base, "FOO=from_base\n")
    _write(child, "FOO=from_child\n")

    manager = InheritManager(base, child)
    result = manager.apply()

    assert "FOO" in result.skipped
    assert result.added == []
    assert "FOO=from_child" in child.read_text()


def test_inherit_overwrite_replaces_existing_key(tmp_dir: Path) -> None:
    base = tmp_dir / "base.env"
    child = tmp_dir / "child.env"
    _write(base, "FOO=new_value\n")
    _write(child, "FOO=old_value\n")

    manager = InheritManager(base, child)
    result = manager.apply(overwrite=True)

    assert "FOO" in result.added
    assert result.skipped == []


def test_inherit_with_prefix(tmp_dir: Path) -> None:
    base = tmp_dir / "base.env"
    child = tmp_dir / "child.env"
    _write(base, "DB_HOST=localhost\n")
    _write(child, "")

    manager = InheritManager(base, child)
    result = manager.apply(prefix="STAGING_")

    assert "STAGING_DB_HOST" in result.added
    assert "STAGING_DB_HOST=localhost" in child.read_text()


def test_inherit_missing_base_raises(tmp_dir: Path) -> None:
    base = tmp_dir / "missing.env"
    child = tmp_dir / "child.env"
    _write(child, "FOO=1\n")

    manager = InheritManager(base, child)
    with pytest.raises(InheritError, match="Base file not found"):
        manager.apply()


def test_inherit_missing_child_raises(tmp_dir: Path) -> None:
    base = tmp_dir / "base.env"
    child = tmp_dir / "missing.env"
    _write(base, "FOO=1\n")

    manager = InheritManager(base, child)
    with pytest.raises(InheritError, match="Child file not found"):
        manager.apply()


def test_inherit_summary_no_changes(tmp_dir: Path) -> None:
    base = tmp_dir / "base.env"
    child = tmp_dir / "child.env"
    _write(base, "FOO=1\n")
    _write(child, "FOO=2\n")

    manager = InheritManager(base, child)
    result = manager.apply()

    assert result.summary() == "1 key(s) skipped (already defined)"
    assert result.changed is False


def test_inherit_summary_with_changes(tmp_dir: Path) -> None:
    base = tmp_dir / "base.env"
    child = tmp_dir / "child.env"
    _write(base, "FOO=1\nBAR=2\n")
    _write(child, "BAR=existing\n")

    manager = InheritManager(base, child)
    result = manager.apply()

    assert "1 key(s) inherited" in result.summary()
    assert "1 key(s) skipped" in result.summary()
