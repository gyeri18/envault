"""Tests for envault.env_stats."""
from pathlib import Path

import pytest

from envault.env_stats import StatsManager, EnvStats
from envault.exceptions import EnvaultError


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_compute_counts_total_keys(tmp_dir):
    f = _write(tmp_dir / ".env", "A=1\nB=2\nC=3\n")
    stats = StatsManager(f).compute()
    assert stats.total_keys == 3


def test_compute_detects_empty_values(tmp_dir):
    f = _write(tmp_dir / ".env", "A=\nB=hello\nC=\n")
    stats = StatsManager(f).compute()
    assert stats.empty_values == 2


def test_compute_counts_commented_lines(tmp_dir):
    f = _write(tmp_dir / ".env", "# comment\nA=1\n# another\n")
    stats = StatsManager(f).compute()
    assert stats.commented_lines == 2
    assert stats.total_keys == 1


def test_compute_counts_blank_lines(tmp_dir):
    f = _write(tmp_dir / ".env", "A=1\n\n\nB=2\n")
    stats = StatsManager(f).compute()
    assert stats.blank_lines == 2


def test_compute_detects_duplicate_keys(tmp_dir):
    f = _write(tmp_dir / ".env", "A=1\nA=2\nB=3\n")
    stats = StatsManager(f).compute()
    assert "A" in stats.duplicate_keys
    assert "B" not in stats.duplicate_keys


def test_unique_keys_excludes_duplicates(tmp_dir):
    f = _write(tmp_dir / ".env", "A=1\nA=2\nB=3\n")
    stats = StatsManager(f).compute()
    # total=3, duplicates=[A] => unique=2
    assert stats.unique_keys == 2


def test_longest_key(tmp_dir):
    f = _write(tmp_dir / ".env", "SHORT=1\nVERY_LONG_KEY_NAME=2\n")
    stats = StatsManager(f).compute()
    assert stats.longest_key == "VERY_LONG_KEY_NAME"


def test_longest_value_key(tmp_dir):
    f = _write(tmp_dir / ".env", "A=hi\nB=this_is_a_long_value\n")
    stats = StatsManager(f).compute()
    assert stats.longest_value_key == "B"


def test_summary_contains_expected_fields(tmp_dir):
    f = _write(tmp_dir / ".env", "A=1\nB=\n# comment\n\n")
    summary = StatsManager(f).compute().summary()
    assert "Total keys" in summary
    assert "Empty values" in summary
    assert "Commented lines" in summary


def test_missing_file_raises(tmp_dir):
    with pytest.raises(EnvaultError, match="File not found"):
        StatsManager(tmp_dir / "nonexistent.env").compute()


def test_empty_file_returns_zero_stats(tmp_dir):
    f = _write(tmp_dir / ".env", "")
    stats = StatsManager(f).compute()
    assert stats.total_keys == 0
    assert stats.blank_lines == 0
