"""Tests for envault.env_encrypt_all."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.env_encrypt_all import EncryptAllManager, EncryptAllResult, EncryptAllError


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str = "KEY=value\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---------------------------------------------------------------------------
# EncryptAllResult
# ---------------------------------------------------------------------------

def test_result_ok_when_no_failures():
    r = EncryptAllResult(encrypted=[Path("a")], skipped=[], failed=[])
    assert r.ok is True


def test_result_not_ok_when_failures():
    r = EncryptAllResult(encrypted=[], skipped=[], failed=[(Path("a"), "boom")])
    assert r.ok is False


def test_result_summary_contains_counts():
    r = EncryptAllResult(
        encrypted=[Path("a"), Path("b")],
        skipped=[Path("c")],
        failed=[],
    )
    summary = r.summary()
    assert "2" in summary
    assert "1" in summary


# ---------------------------------------------------------------------------
# EncryptAllManager
# ---------------------------------------------------------------------------

def test_raises_when_root_is_not_a_directory(tmp_dir):
    fake_file = tmp_dir / "not_a_dir"
    fake_file.write_text("x")
    manager = EncryptAllManager()
    with pytest.raises(EncryptAllError, match="not a directory"):
        manager.encrypt_all(root=fake_file)


def test_skips_already_locked_files(tmp_dir):
    env_file = tmp_dir / ".env"
    vault_file = tmp_dir / ".vault"
    _write(env_file)
    vault_file.write_text("locked")

    manager = EncryptAllManager()
    result = manager.encrypt_all(root=tmp_dir, skip_already_locked=True)

    assert env_file in result.skipped
    assert not result.encrypted


def test_includes_locked_files_when_flag_set(tmp_dir):
    env_file = tmp_dir / ".env"
    vault_file = tmp_dir / ".vault"
    _write(env_file)
    vault_file.write_text("locked")

    mock_vm = MagicMock()
    with patch("envault.env_encrypt_all.VaultManager", return_value=mock_vm):
        manager = EncryptAllManager()
        result = manager.encrypt_all(root=tmp_dir, skip_already_locked=False)

    assert env_file in result.encrypted
    assert not result.skipped


def test_failed_files_captured_in_result(tmp_dir):
    env_file = tmp_dir / ".env"
    _write(env_file)

    with patch("envault.env_encrypt_all.VaultManager", side_effect=RuntimeError("bad")):
        manager = EncryptAllManager()
        result = manager.encrypt_all(root=tmp_dir)

    assert len(result.failed) == 1
    assert result.failed[0][0] == env_file
    assert "bad" in result.failed[0][1]


def test_encrypt_all_empty_directory_returns_empty_result(tmp_dir):
    manager = EncryptAllManager()
    result = manager.encrypt_all(root=tmp_dir)
    assert result.ok
    assert not result.encrypted
    assert not result.skipped
    assert not result.failed
