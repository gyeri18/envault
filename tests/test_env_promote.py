"""Tests for envault.env_promote."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_promote import PromoteError, PromoteManager, PromoteResult


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture()
def manager() -> PromoteManager:
    return PromoteManager()


# ── PromoteResult ─────────────────────────────────────────────────────────────

def test_result_changed_false_when_nothing_moved():
    r = PromoteResult(skipped=["A"])
    assert not r.changed


def test_result_changed_true_when_promoted():
    r = PromoteResult(promoted=["A"])
    assert r.changed


def test_result_summary_nothing():
    assert PromoteResult().summary() == "nothing to promote"


def test_result_summary_counts():
    r = PromoteResult(promoted=["A", "B"], overwritten=["C"], skipped=["D"])
    assert "2 promoted" in r.summary()
    assert "1 overwritten" in r.summary()
    assert "1 skipped" in r.summary()


# ── PromoteManager.promote ────────────────────────────────────────────────────

def test_promote_new_keys(tmp_dir, manager):
    src = tmp_dir / ".env.staging"
    dst = tmp_dir / ".env.prod"
    _write(src, "FOO=bar\nBAZ=qux\n")
    _write(dst, "EXISTING=1\n")

    result = manager.promote(src, dst)

    assert "FOO" in result.promoted
    assert "BAZ" in result.promoted
    assert result.skipped == []
    assert dst.read_text().count("FOO=bar") == 1


def test_promote_skips_existing_without_overwrite(tmp_dir, manager):
    src = tmp_dir / ".env.staging"
    dst = tmp_dir / ".env.prod"
    _write(src, "FOO=new_value\n")
    _write(dst, "FOO=old_value\n")

    result = manager.promote(src, dst)

    assert "FOO" in result.skipped
    assert "old_value" in dst.read_text()


def test_promote_overwrites_when_flag_set(tmp_dir, manager):
    src = tmp_dir / ".env.staging"
    dst = tmp_dir / ".env.prod"
    _write(src, "FOO=new_value\n")
    _write(dst, "FOO=old_value\n")

    result = manager.promote(src, dst, overwrite=True)

    assert "FOO" in result.overwritten
    assert "new_value" in dst.read_text()


def test_promote_selected_keys_only(tmp_dir, manager):
    src = tmp_dir / ".env.staging"
    dst = tmp_dir / ".env.prod"
    _write(src, "FOO=1\nBAR=2\nBAZ=3\n")
    _write(dst, "")

    result = manager.promote(src, dst, keys=["FOO", "BAZ"])

    assert result.promoted == ["FOO", "BAZ"]
    content = dst.read_text()
    assert "FOO=1" in content
    assert "BAZ=3" in content
    assert "BAR" not in content


def test_promote_missing_source_raises(tmp_dir, manager):
    dst = tmp_dir / ".env.prod"
    _write(dst, "")
    with pytest.raises(PromoteError, match="Source file not found"):
        manager.promote(tmp_dir / "nonexistent.env", dst)


def test_promote_missing_destination_raises(tmp_dir, manager):
    src = tmp_dir / ".env.staging"
    _write(src, "FOO=1\n")
    with pytest.raises(PromoteError, match="Destination file not found"):
        manager.promote(src, tmp_dir / "nonexistent.env")


def test_promote_missing_selected_key_raises(tmp_dir, manager):
    src = tmp_dir / ".env.staging"
    dst = tmp_dir / ".env.prod"
    _write(src, "FOO=1\n")
    _write(dst, "")
    with pytest.raises(PromoteError, match="Key 'MISSING'"):
        manager.promote(src, dst, keys=["MISSING"])
