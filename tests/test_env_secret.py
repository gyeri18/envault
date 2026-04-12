"""Tests for envault.env_secret."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_secret import SecretError, SecretFinding, SecretManager, SecretScanResult, _shannon_entropy


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_shannon_entropy_empty_string():
    assert _shannon_entropy("") == 0.0


def test_shannon_entropy_uniform():
    # All same characters → entropy 0
    assert _shannon_entropy("aaaa") == 0.0


def test_shannon_entropy_high_for_random_string():
    val = "aB3$xZ9!qW2@eR5#"
    assert _shannon_entropy(val) > 3.0


# ---------------------------------------------------------------------------
# SecretManager.scan
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager() -> SecretManager:
    return SecretManager()


def test_scan_missing_file_raises(manager: SecretManager, tmp_dir: Path):
    with pytest.raises(SecretError):
        manager.scan(tmp_dir / "nonexistent.env")


def test_scan_clean_file_returns_ok(manager: SecretManager, tmp_dir: Path):
    env = _write(tmp_dir / ".env", "APP_NAME=myapp\nDEBUG=true\n")
    result = manager.scan(env)
    assert result.ok
    assert result.summary() == "No secrets detected."


def test_scan_detects_key_named_password(manager: SecretManager, tmp_dir: Path):
    env = _write(tmp_dir / ".env", "DB_PASSWORD=hunter2\n")
    result = manager.scan(env)
    assert not result.ok
    assert any(f.key == "DB_PASSWORD" for f in result.findings)


def test_scan_detects_high_entropy_value(manager: SecretManager, tmp_dir: Path):
    # 40-char hex string — high entropy AND matches hex pattern
    secret = "a" * 5 + "1b2c3d4e5f" * 3 + "abcdef1234"
    env = _write(tmp_dir / ".env", f"SOME_VALUE={secret}\n")
    result = manager.scan(env)
    assert not result.ok


def test_scan_ignores_comments_and_blank_lines(manager: SecretManager, tmp_dir: Path):
    env = _write(tmp_dir / ".env", "# DB_PASSWORD=secret\n\nAPP=ok\n")
    result = manager.scan(env)
    assert result.ok


def test_scan_ignores_empty_values(manager: SecretManager, tmp_dir: Path):
    env = _write(tmp_dir / ".env", "API_KEY=\n")
    result = manager.scan(env)
    assert result.ok


def test_scan_result_summary_plural(manager: SecretManager, tmp_dir: Path):
    env = _write(tmp_dir / ".env", "API_KEY=abc\nSECRET_TOKEN=xyz\n")
    result = manager.scan(env)
    # Both keys match the pattern
    assert "secret(s)" in result.summary()


def test_finding_str_contains_key_and_reason():
    f = SecretFinding(line_number=3, key="MY_KEY", reason="high entropy (4.20)")
    s = str(f)
    assert "MY_KEY" in s
    assert "high entropy" in s
    assert "3" in s


def test_custom_entropy_threshold(tmp_dir: Path):
    # With a very high threshold, entropy alone won't flag anything
    manager = SecretManager(entropy_threshold=10.0)
    secret = "aB3$xZ9!qW2@eR5#tY6&uI8*"
    env = _write(tmp_dir / ".env", f"SOME_VALUE={secret}\n")
    result = manager.scan(env)
    # No pattern match on key name and entropy below absurd threshold
    assert result.ok
