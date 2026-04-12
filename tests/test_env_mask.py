"""Tests for envault.env_mask."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_mask import MaskError, MaskManager


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    return _write(
        tmp_dir / ".env",
        "DB_HOST=localhost\nDB_PASSWORD=supersecret\nAPI_KEY=abc123xyz\nAPP_NAME=myapp\n",
    )


@pytest.fixture()
def manager() -> MaskManager:
    return MaskManager(show_chars=4)


def test_mask_sensitive_key_by_auto_detect(env_file: Path, manager: MaskManager) -> None:
    result = manager.mask_file(env_file)
    text = result.as_text()
    assert "DB_PASSWORD=supe****" in text
    assert "API_KEY=abc1***" in text


def test_non_sensitive_key_unchanged(env_file: Path, manager: MaskManager) -> None:
    result = manager.mask_file(env_file)
    assert "APP_NAME=myapp" in result.as_text()
    assert "DB_HOST=localhost" in result.as_text()


def test_masked_keys_list_populated(env_file: Path, manager: MaskManager) -> None:
    result = manager.mask_file(env_file)
    assert "DB_PASSWORD" in result.masked_keys
    assert "API_KEY" in result.masked_keys
    assert "APP_NAME" not in result.masked_keys


def test_explicit_key_masked_even_if_not_sensitive(env_file: Path, manager: MaskManager) -> None:
    result = manager.mask_file(env_file, keys=["APP_NAME"])
    assert "APP_NAME=myap*" in result.as_text()
    assert "APP_NAME" in result.masked_keys


def test_no_auto_detect_skips_sensitive(env_file: Path, manager: MaskManager) -> None:
    result = manager.mask_file(env_file, auto_detect=False)
    assert "DB_PASSWORD=supersecret" in result.as_text()
    assert not result.masked_keys


def test_missing_file_raises(tmp_dir: Path, manager: MaskManager) -> None:
    with pytest.raises(MaskError, match="File not found"):
        manager.mask_file(tmp_dir / "missing.env")


def test_comments_and_blank_lines_preserved(tmp_dir: Path, manager: MaskManager) -> None:
    p = _write(tmp_dir / ".env", "# comment\n\nFOO=bar\n")
    result = manager.mask_file(p)
    assert "# comment" in result.lines
    assert "" in result.lines


def test_short_value_fully_masked(manager: MaskManager) -> None:
    result = manager.mask_text("SECRET=ab")
    assert "SECRET=**" in result.as_text()


def test_mask_dict_masks_sensitive_keys(manager: MaskManager) -> None:
    data = {"API_TOKEN": "abcdefgh", "HOST": "localhost"}
    out = manager.mask_dict(data)
    assert out["API_TOKEN"] == "abcd****"
    assert out["HOST"] == "localhost"


def test_mask_dict_explicit_keys(manager: MaskManager) -> None:
    data = {"HOST": "localhost"}
    out = manager.mask_dict(data, keys=["HOST"], auto_detect=False)
    assert out["HOST"] == "loca*****"
