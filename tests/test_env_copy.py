"""Tests for envault.env_copy.CopyManager."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.env_copy import CopyManager
from envault.exceptions import EnvaultError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_pairs(path: Path) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            pairs[k.strip()] = v.strip()
    return pairs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_copy_all_keys(tmp_dir: Path) -> None:
    src = _write(tmp_dir / "src.env", "FOO=bar\nBAZ=qux\n")
    dst = tmp_dir / "dst.env"
    manager = CopyManager(tmp_dir)
    written = manager.copy(src, dst)
    assert set(written) == {"FOO", "BAZ"}
    pairs = _read_pairs(dst)
    assert pairs["FOO"] == "bar"
    assert pairs["BAZ"] == "qux"


def test_copy_selected_keys(tmp_dir: Path) -> None:
    src = _write(tmp_dir / "src.env", "FOO=1\nBAR=2\nBAZ=3\n")
    dst = tmp_dir / "dst.env"
    manager = CopyManager(tmp_dir)
    written = manager.copy(src, dst, keys=["FOO", "BAZ"])
    assert written == ["FOO", "BAZ"]
    pairs = _read_pairs(dst)
    assert "BAR" not in pairs


def test_copy_missing_key_raises(tmp_dir: Path) -> None:
    src = _write(tmp_dir / "src.env", "FOO=1\n")
    dst = tmp_dir / "dst.env"
    manager = CopyManager(tmp_dir)
    with pytest.raises(EnvaultError, match="MISSING"):
        manager.copy(src, dst, keys=["MISSING"])


def test_copy_missing_src_raises(tmp_dir: Path) -> None:
    manager = CopyManager(tmp_dir)
    with pytest.raises(EnvaultError, match="Source file not found"):
        manager.copy(tmp_dir / "nonexistent.env", tmp_dir / "dst.env")


def test_copy_overwrite_false_preserves_existing(tmp_dir: Path) -> None:
    src = _write(tmp_dir / "src.env", "FOO=new\nBAR=src_bar\n")
    dst = _write(tmp_dir / "dst.env", "FOO=old\n")
    manager = CopyManager(tmp_dir)
    written = manager.copy(src, dst, overwrite=False)
    assert "FOO" not in written  # skipped because overwrite=False
    assert "BAR" in written
    pairs = _read_pairs(dst)
    assert pairs["FOO"] == "old"   # preserved
    assert pairs["BAR"] == "src_bar"


def test_copy_overwrite_true_replaces_existing(tmp_dir: Path) -> None:
    src = _write(tmp_dir / "src.env", "FOO=new\n")
    dst = _write(tmp_dir / "dst.env", "FOO=old\n")
    manager = CopyManager(tmp_dir)
    manager.copy(src, dst, overwrite=True)
    pairs = _read_pairs(dst)
    assert pairs["FOO"] == "new"


def test_copy_ignores_comments_and_blank_lines(tmp_dir: Path) -> None:
    src = _write(tmp_dir / "src.env", "# comment\n\nFOO=bar\n")
    dst = tmp_dir / "dst.env"
    manager = CopyManager(tmp_dir)
    written = manager.copy(src, dst)
    assert written == ["FOO"]
