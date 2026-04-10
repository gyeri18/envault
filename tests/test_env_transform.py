"""Tests for envault.env_transform."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_transform import TransformManager, TransformError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def _read_pairs(path: Path) -> dict:
    pairs = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            pairs[k.strip()] = v.strip()
    return pairs


def test_transform_upper(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "APP_NAME=hello\nDB_HOST=localhost\n")
    mgr = TransformManager(f)
    changed = mgr.transform("upper")
    assert changed["APP_NAME"] == ("hello", "HELLO")
    assert changed["DB_HOST"] == ("localhost", "LOCALHOST")
    pairs = _read_pairs(f)
    assert pairs["APP_NAME"] == "HELLO"


def test_transform_lower(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "KEY=WORLD\n")
    mgr = TransformManager(f)
    mgr.transform("lower")
    assert _read_pairs(f)["KEY"] == "world"


def test_transform_specific_keys_only(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "A=hello\nB=world\n")
    mgr = TransformManager(f)
    changed = mgr.transform("upper", keys=["A"])
    assert "A" in changed
    assert "B" not in changed
    pairs = _read_pairs(f)
    assert pairs["A"] == "HELLO"
    assert pairs["B"] == "world"


def test_transform_by_pattern(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    mgr = TransformManager(f)
    changed = mgr.transform("upper", pattern="^DB_")
    assert "DB_HOST" in changed
    assert "DB_PORT" in changed
    assert "APP_NAME" not in changed


def test_transform_dry_run_does_not_write(tmp_dir):
    f = tmp_dir / ".env"
    original = "KEY=hello\n"
    _write(f, original)
    mgr = TransformManager(f)
    changed = mgr.transform("upper", dry_run=True)
    assert changed["KEY"] == ("hello", "HELLO")
    assert f.read_text() == original  # file unchanged


def test_transform_unknown_operation_raises(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "KEY=value\n")
    mgr = TransformManager(f)
    with pytest.raises(TransformError, match="Unknown transform"):
        mgr.transform("nonexistent")


def test_transform_quote_and_unquote(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "SECRET=mypassword\n")
    mgr = TransformManager(f)
    mgr.transform("quote")
    assert _read_pairs(f)["SECRET"] == '"mypassword"'
    mgr.transform("unquote")
    assert _read_pairs(f)["SECRET"] == "mypassword"


def test_available_transforms_returns_list(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "")
    mgr = TransformManager(f)
    ops = mgr.available_transforms()
    assert "upper" in ops
    assert "lower" in ops
    assert "base64encode" in ops


def test_comments_preserved_after_transform(tmp_dir):
    f = tmp_dir / ".env"
    _write(f, "# comment\nKEY=hello\n")
    mgr = TransformManager(f)
    mgr.transform("upper")
    content = f.read_text()
    assert "# comment" in content
    assert "KEY=HELLO" in content
