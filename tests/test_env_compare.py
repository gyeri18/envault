"""Tests for envault.env_compare."""
import pytest
from pathlib import Path

from envault.env_compare import CompareManager, CompareResult
from envault.exceptions import EnvaultError


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture
def manager() -> CompareManager:
    return CompareManager()


def test_compare_identical_files(tmp_dir: Path, manager: CompareManager) -> None:
    content = "KEY1=val1\nKEY2=val2\n"
    a = _write(tmp_dir / "a.env", content)
    b = _write(tmp_dir / "b.env", content)
    result = manager.compare_files(a, b)
    assert not result.has_differences
    assert set(result.unchanged) == {"KEY1", "KEY2"}


def test_compare_detects_added_key(tmp_dir: Path, manager: CompareManager) -> None:
    a = _write(tmp_dir / "a.env", "KEY1=val1\n")
    b = _write(tmp_dir / "b.env", "KEY1=val1\nKEY2=val2\n")
    result = manager.compare_files(a, b)
    assert "KEY2" in result.only_in_b
    assert result.only_in_b["KEY2"] == "val2"


def test_compare_detects_removed_key(tmp_dir: Path, manager: CompareManager) -> None:
    a = _write(tmp_dir / "a.env", "KEY1=val1\nKEY2=val2\n")
    b = _write(tmp_dir / "b.env", "KEY1=val1\n")
    result = manager.compare_files(a, b)
    assert "KEY2" in result.only_in_a


def test_compare_detects_changed_value(tmp_dir: Path, manager: CompareManager) -> None:
    a = _write(tmp_dir / "a.env", "KEY1=old\n")
    b = _write(tmp_dir / "b.env", "KEY1=new\n")
    result = manager.compare_files(a, b)
    assert "KEY1" in result.changed
    assert result.changed["KEY1"] == ("old", "new")


def test_redact_hides_values(tmp_dir: Path) -> None:
    mgr = CompareManager(redact=True)
    a = _write(tmp_dir / "a.env", "KEY1=secret\n")
    b = _write(tmp_dir / "b.env", "KEY2=other_secret\n")
    result = mgr.compare_files(a, b)
    assert result.only_in_a["KEY1"] == "***"
    assert result.only_in_b["KEY2"] == "***"


def test_missing_file_raises(tmp_dir: Path, manager: CompareManager) -> None:
    a = _write(tmp_dir / "a.env", "KEY=val\n")
    with pytest.raises(EnvaultError, match="not found"):
        manager.compare_files(a, tmp_dir / "nonexistent.env")


def test_summary_no_diff(manager: CompareManager) -> None:
    result = CompareResult()
    assert result.summary() == "No differences found."


def test_summary_with_diff(manager: CompareManager) -> None:
    result = CompareResult(
        only_in_a={"OLD": "v"},
        only_in_b={"NEW": "v"},
        changed={"MOD": ("a", "b")},
    )
    summary = result.summary()
    assert "- OLD=v" in summary
    assert "+ NEW=v" in summary
    assert "~ MOD" in summary


def test_compare_dicts_directly(manager: CompareManager) -> None:
    env_a = {"A": "1", "B": "2"}
    env_b = {"A": "1", "C": "3"}
    result = manager.compare_dicts(env_a, env_b)
    assert "B" in result.only_in_a
    assert "C" in result.only_in_b
    assert "A" in result.unchanged
