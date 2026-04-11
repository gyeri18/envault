"""Tests for envault.env_placeholder."""
import pytest
from pathlib import Path
from envault.env_placeholder import PlaceholderManager, PlaceholderError


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


@pytest.fixture
def env_file(tmp_dir: Path) -> Path:
    return tmp_dir / ".env"


@pytest.fixture
def manager(env_file: Path) -> PlaceholderManager:
    return PlaceholderManager(env_file)


def test_scan_no_placeholders(manager, env_file):
    _write(env_file, "KEY=value\nFOO=bar\n")
    result = manager.scan()
    assert result.ok
    assert result.issues == []


def test_scan_detects_angle_bracket_placeholder(manager, env_file):
    _write(env_file, "API_KEY=<YOUR_API_KEY>\n")
    result = manager.scan()
    assert not result.ok
    assert len(result.issues) == 1
    assert result.issues[0].key == "API_KEY"
    assert result.issues[0].placeholder == "YOUR_API_KEY"
    assert result.issues[0].line_number == 1


def test_scan_detects_dollar_brace_placeholder(manager, env_file):
    _write(env_file, "DB_URL=${DATABASE_URL}\n")
    result = manager.scan()
    assert not result.ok
    assert result.issues[0].placeholder == "DATABASE_URL"


def test_scan_detects_double_brace_placeholder(manager, env_file):
    _write(env_file, "SECRET={{MY_SECRET}}\n")
    result = manager.scan()
    assert not result.ok
    assert result.issues[0].placeholder == "MY_SECRET"


def test_scan_skips_comments_and_blank_lines(manager, env_file):
    _write(env_file, "# comment\n\nREAL=value\n")
    result = manager.scan()
    assert result.ok


def test_scan_multiple_placeholders(manager, env_file):
    _write(env_file, "A=<PLACEHOLDER_A>\nB=real\nC=${PLACEHOLDER_C}\n")
    result = manager.scan()
    assert len(result.issues) == 2
    keys = {i.key for i in result.issues}
    assert keys == {"A", "C"}


def test_scan_missing_file_raises(tmp_dir):
    manager = PlaceholderManager(tmp_dir / "nonexistent.env")
    with pytest.raises(PlaceholderError):
        manager.scan()


def test_resolve_fills_known_placeholder(manager, env_file):
    _write(env_file, "API_KEY=<YOUR_API_KEY>\n")
    result = manager.resolve({"YOUR_API_KEY": "abc123"})
    assert result.ok
    assert result.resolved["API_KEY"] == "abc123"
    assert "abc123" in env_file.read_text()


def test_resolve_leaves_unknown_placeholder_as_issue(manager, env_file):
    _write(env_file, "API_KEY=<UNKNOWN>\n")
    result = manager.resolve({})
    assert not result.ok
    assert result.issues[0].key == "API_KEY"
    assert result.resolved == {}


def test_resolve_partial(manager, env_file):
    _write(env_file, "A=<FILL_A>\nB=<FILL_B>\n")
    result = manager.resolve({"FILL_A": "hello"})
    assert len(result.issues) == 1
    assert result.issues[0].key == "B"
    assert result.resolved == {"A": "hello"}


def test_placeholder_issue_str(manager, env_file):
    _write(env_file, "TOKEN=<SECRET_TOKEN>\n")
    result = manager.scan()
    assert "TOKEN" in str(result.issues[0])
    assert "SECRET_TOKEN" in str(result.issues[0])
    assert "1" in str(result.issues[0])
