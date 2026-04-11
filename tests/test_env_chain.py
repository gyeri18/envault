"""Tests for envault.env_chain."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_chain import ChainManager, ChainError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def manager(tmp_dir: Path) -> ChainManager:
    return ChainManager(base_dir=tmp_dir)


def test_chain_single_file(tmp_dir: Path, manager: ChainManager) -> None:
    _write(tmp_dir / "base.env", "FOO=bar\nBAZ=qux\n")
    result = manager.chain(["base.env"])
    assert result.merged == {"FOO": "bar", "BAZ": "qux"}


def test_chain_later_file_overrides(tmp_dir: Path, manager: ChainManager) -> None:
    _write(tmp_dir / "base.env", "FOO=base\nSHARED=base\n")
    _write(tmp_dir / "override.env", "SHARED=override\nNEW=value\n")
    result = manager.chain(["base.env", "override.env"])
    assert result.merged["SHARED"] == "override"
    assert result.merged["FOO"] == "base"
    assert result.merged["NEW"] == "value"


def test_chain_sources_track_winning_file(tmp_dir: Path, manager: ChainManager) -> None:
    _write(tmp_dir / "a.env", "KEY=a\n")
    _write(tmp_dir / "b.env", "KEY=b\n")
    result = manager.chain(["a.env", "b.env"])
    assert str(tmp_dir / "b.env") == result.sources["KEY"]


def test_chain_skips_comments_and_blanks(tmp_dir: Path, manager: ChainManager) -> None:
    _write(tmp_dir / "c.env", "# comment\n\nFOO=1\n")
    result = manager.chain(["c.env"])
    assert list(result.merged.keys()) == ["FOO"]


def test_chain_missing_file_raises(tmp_dir: Path, manager: ChainManager) -> None:
    with pytest.raises(ChainError, match="not found"):
        manager.chain(["nonexistent.env"])


def test_chain_empty_list_raises(manager: ChainManager) -> None:
    with pytest.raises(ChainError, match="At least one"):
        manager.chain([])


def test_write_creates_file(tmp_dir: Path, manager: ChainManager) -> None:
    _write(tmp_dir / "src.env", "A=1\nB=2\n")
    result = manager.chain(["src.env"])
    dest = manager.write(result, tmp_dir / "merged.env")
    assert dest.exists()
    content = dest.read_text()
    assert "A=1" in content
    assert "B=2" in content


def test_key_count_property(tmp_dir: Path, manager: ChainManager) -> None:
    _write(tmp_dir / "k.env", "X=1\nY=2\nZ=3\n")
    result = manager.chain(["k.env"])
    assert result.key_count == 3
