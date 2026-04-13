"""Tests for envault.env_dedup."""
from pathlib import Path

import pytest

from envault.env_dedup import DedupError, DedupManager, DedupResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def manager() -> DedupManager:
    return DedupManager()


# ---------------------------------------------------------------------------
# DedupResult helpers
# ---------------------------------------------------------------------------

def test_dedup_result_changed_false_when_no_removals():
    r = DedupResult(kept={"A": "1"})
    assert r.changed is False


def test_dedup_result_changed_true_when_removals():
    r = DedupResult(removed=[("A", "old")], kept={"A": "new"})
    assert r.changed is True


def test_dedup_result_summary_no_changes():
    r = DedupResult()
    assert "No duplicate" in r.summary


def test_dedup_result_summary_lists_keys():
    r = DedupResult(removed=[("FOO", "1"), ("FOO", "2")], kept={"FOO": "3"})
    assert "FOO" in r.summary
    assert "2" in r.summary  # count


# ---------------------------------------------------------------------------
# deduplicate — keep="last" (default)
# ---------------------------------------------------------------------------

def test_no_duplicates_returns_unchanged(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "A=1\nB=2\n")
    result = manager.deduplicate(str(f))
    assert result.changed is False
    assert f.read_text() == "A=1\nB=2\n"


def test_dedup_keeps_last_by_default(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "A=first\nB=2\nA=last\n")
    result = manager.deduplicate(str(f))
    assert result.changed is True
    assert ("A", "first") in result.removed
    content = f.read_text()
    assert content.count("A=") == 1
    assert "A=last" in content


def test_dedup_keeps_first_when_specified(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "A=first\nB=2\nA=last\n")
    result = manager.deduplicate(str(f), keep="first")
    assert result.changed is True
    assert ("A", "last") in result.removed
    content = f.read_text()
    assert "A=first" in content


def test_dedup_preserves_comments(tmp_dir, manager):
    content = "# comment\nA=1\n# another\nA=2\n"
    f = _write(tmp_dir / ".env", content)
    result = manager.deduplicate(str(f))
    assert result.changed is True
    kept = f.read_text()
    assert "# comment" in kept
    assert "# another" in kept


def test_dedup_multiple_duplicate_keys(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "X=1\nY=a\nX=2\nY=b\nX=3\n")
    result = manager.deduplicate(str(f))
    assert len(result.removed) == 3  # two X + one Y
    content = f.read_text()
    assert content.count("X=") == 1
    assert content.count("Y=") == 1


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_file_raises(tmp_dir, manager):
    with pytest.raises(DedupError, match="File not found"):
        manager.deduplicate(str(tmp_dir / "nonexistent.env"))


def test_invalid_keep_strategy_raises(tmp_dir, manager):
    f = _write(tmp_dir / ".env", "A=1\n")
    with pytest.raises(DedupError, match="Invalid keep strategy"):
        manager.deduplicate(str(f), keep="middle")
