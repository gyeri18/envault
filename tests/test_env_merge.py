"""Tests for envault.env_merge."""
from pathlib import Path

import pytest

from envault.env_merge import (
    EnvMergeManager,
    MergeConflictError,
    MergeStrategy,
)
from envault.exceptions import EnvaultError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def manager() -> EnvMergeManager:
    return EnvMergeManager()


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_merge_adds_new_keys(manager, tmp_dir):
    base = _write(tmp_dir / "base.env", "A=1\nB=2\n")
    incoming = _write(tmp_dir / "incoming.env", "C=3\n")
    out = tmp_dir / "out.env"
    result = manager.merge(base, incoming, out)
    assert result.merged == {"A": "1", "B": "2", "C": "3"}
    assert out.exists()


def test_merge_ours_keeps_base_on_conflict(manager, tmp_dir):
    base = _write(tmp_dir / "base.env", "A=base_val\n")
    incoming = _write(tmp_dir / "incoming.env", "A=new_val\n")
    out = tmp_dir / "out.env"
    result = manager.merge(base, incoming, out, strategy=MergeStrategy.OURS)
    assert result.merged["A"] == "base_val"
    assert len(result.conflicts) == 1
    assert result.conflicts[0].key == "A"


def test_merge_theirs_takes_incoming_on_conflict(manager, tmp_dir):
    base = _write(tmp_dir / "base.env", "A=base_val\n")
    incoming = _write(tmp_dir / "incoming.env", "A=new_val\n")
    out = tmp_dir / "out.env"
    result = manager.merge(base, incoming, out, strategy=MergeStrategy.THEIRS)
    assert result.merged["A"] == "new_val"


def test_merge_prompt_raises_on_conflict(manager, tmp_dir):
    base = _write(tmp_dir / "base.env", "A=1\nB=2\n")
    incoming = _write(tmp_dir / "incoming.env", "A=99\nB=88\n")
    out = tmp_dir / "out.env"
    with pytest.raises(MergeConflictError) as exc_info:
        manager.merge(base, incoming, out, strategy=MergeStrategy.PROMPT)
    assert len(exc_info.value.conflicts) == 2


def test_merge_no_conflicts_when_values_identical(manager, tmp_dir):
    base = _write(tmp_dir / "base.env", "A=same\n")
    incoming = _write(tmp_dir / "incoming.env", "A=same\n")
    out = tmp_dir / "out.env"
    result = manager.merge(base, incoming, out)
    assert result.conflicts == []
    assert result.merged["A"] == "same"


def test_merge_writes_output_file(manager, tmp_dir):
    base = _write(tmp_dir / "base.env", "X=10\n")
    incoming = _write(tmp_dir / "incoming.env", "Y=20\n")
    out = tmp_dir / "out.env"
    manager.merge(base, incoming, out)
    content = out.read_text()
    assert "X=10" in content
    assert "Y=20" in content


def test_merge_missing_base_raises(manager, tmp_dir):
    incoming = _write(tmp_dir / "incoming.env", "A=1\n")
    out = tmp_dir / "out.env"
    with pytest.raises(EnvaultError, match="File not found"):
        manager.merge(tmp_dir / "missing.env", incoming, out)


def test_merge_skips_comments_and_blank_lines(manager, tmp_dir):
    base = _write(tmp_dir / "base.env", "# comment\n\nA=1\n")
    incoming = _write(tmp_dir / "incoming.env", "B=2\n")
    out = tmp_dir / "out.env"
    result = manager.merge(base, incoming, out)
    assert "A" in result.merged
    assert "B" in result.merged
    assert len(result.merged) == 2
