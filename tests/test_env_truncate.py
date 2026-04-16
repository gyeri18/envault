"""Tests for env_truncate module."""
import pytest
from pathlib import Path
from envault.env_truncate import TruncateManager, TruncateResult, TruncateError


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def test_truncate_result_changed_false_when_no_truncations():
    r = TruncateResult(pairs={"A": "short"}, truncated_keys=[])
    assert not r.changed


def test_truncate_result_changed_true_when_truncations():
    r = TruncateResult(pairs={"A": "x..."}, truncated_keys=["A"])
    assert r.changed


def test_truncate_result_summary_no_changes():
    r = TruncateResult()
    assert "No values" in r.summary()


def test_truncate_result_summary_lists_keys():
    r = TruncateResult(pairs={"SECRET": "abc..."}, truncated_keys=["SECRET"])
    assert "SECRET" in r.summary()
    assert "1" in r.summary()


def test_truncate_short_values_unchanged(tmp_dir):
    f = _write(tmp_dir / ".env", "KEY=short\nOTHER=value\n")
    manager = TruncateManager(max_length=40)
    result = manager.truncate(f)
    assert result.pairs["KEY"] == "short"
    assert not result.changed


def test_truncate_long_value_is_cut(tmp_dir):
    long_val = "A" * 80
    f = _write(tmp_dir / ".env", f"SECRET={long_val}\n")
    manager = TruncateManager(max_length=20)
    result = manager.truncate(f)
    assert result.pairs["SECRET"].endswith("...")
    assert len(result.pairs["SECRET"]) == 20
    assert "SECRET" in result.truncated_keys


def test_truncate_skips_comments_and_blanks(tmp_dir):
    f = _write(tmp_dir / ".env", "# comment\n\nKEY=val\n")
    manager = TruncateManager()
    result = manager.truncate(f)
    assert list(result.pairs.keys()) == ["KEY"]


def test_truncate_missing_file_raises(tmp_dir):
    manager = TruncateManager()
    with pytest.raises(TruncateError, match="not found"):
        manager.truncate(tmp_dir / "missing.env")


def test_truncate_invalid_max_length_raises():
    with pytest.raises(TruncateError):
        TruncateManager(max_length=2)


def test_truncate_as_text_marks_truncated(tmp_dir):
    long_val = "B" * 60
    f = _write(tmp_dir / ".env", f"TOKEN={long_val}\nSHORT=hi\n")
    manager = TruncateManager(max_length=20)
    result = manager.truncate(f)
    text = result.as_text()
    assert "* TOKEN=" in text
    assert "  SHORT=hi" in text


def test_truncate_exact_length_not_truncated(tmp_dir):
    val = "X" * 40
    f = _write(tmp_dir / ".env", f"KEY={val}\n")
    manager = TruncateManager(max_length=40)
    result = manager.truncate(f)
    assert result.pairs["KEY"] == val
    assert not result.changed
