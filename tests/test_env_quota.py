"""Tests for envault.env_quota."""
import pytest
from pathlib import Path
from envault.env_quota import QuotaManager, QuotaError, QuotaResult, QuotaViolation, _count_keys


@pytest.fixture()
def manager(tmp_path: Path) -> QuotaManager:
    return QuotaManager(config_dir=tmp_path / "cfg")


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("A=1\nB=2\nC=3\n")
    return p


def test_set_quota_stores_limit(manager: QuotaManager) -> None:
    manager.set_quota("myproject", 10)
    assert manager.get_quota("myproject") == 10


def test_set_quota_overwrites_existing(manager: QuotaManager) -> None:
    manager.set_quota("proj", 5)
    manager.set_quota("proj", 20)
    assert manager.get_quota("proj") == 20


def test_set_quota_empty_name_raises(manager: QuotaManager) -> None:
    with pytest.raises(QuotaError, match="empty"):
        manager.set_quota("", 5)


def test_set_quota_zero_limit_raises(manager: QuotaManager) -> None:
    with pytest.raises(QuotaError, match="at least 1"):
        manager.set_quota("proj", 0)


def test_remove_quota_deletes_entry(manager: QuotaManager) -> None:
    manager.set_quota("proj", 3)
    manager.remove_quota("proj")
    assert manager.get_quota("proj") is None


def test_remove_quota_missing_raises(manager: QuotaManager) -> None:
    with pytest.raises(QuotaError, match="No quota"):
        manager.remove_quota("ghost")


def test_list_quotas_returns_all(manager: QuotaManager) -> None:
    manager.set_quota("a", 1)
    manager.set_quota("b", 2)
    assert manager.list_quotas() == {"a": 1, "b": 2}


def test_count_keys_ignores_comments_and_blank(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("# comment\n\nA=1\nB=2\n")
    assert _count_keys(p) == 2


def test_count_keys_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(QuotaError, match="not found"):
        _count_keys(tmp_path / "missing.env")


def test_check_within_quota_returns_ok(manager: QuotaManager, env_file: Path) -> None:
    manager.set_quota("proj", 5)
    result = manager.check("proj", env_file)
    assert result.ok


def test_check_exceeds_quota_returns_violation(manager: QuotaManager, env_file: Path) -> None:
    manager.set_quota("proj", 2)
    result = manager.check("proj", env_file)
    assert not result.ok
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.current == 3
    assert v.limit == 2


def test_check_no_quota_configured_returns_ok(manager: QuotaManager, env_file: Path) -> None:
    result = manager.check("unregistered", env_file)
    assert result.ok


def test_violation_str_contains_project(manager: QuotaManager) -> None:
    v = QuotaViolation(project="myproj", current=10, limit=5)
    assert "myproj" in str(v)
    assert "10" in str(v)
    assert "5" in str(v)


def test_result_summary_ok(manager: QuotaManager) -> None:
    r = QuotaResult()
    assert "within quota" in r.summary()


def test_result_summary_violations(manager: QuotaManager) -> None:
    v = QuotaViolation(project="p", current=6, limit=3)
    r = QuotaResult(violations=[v])
    assert "p" in r.summary()
