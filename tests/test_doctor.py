"""Tests for envault.doctor and envault.cli_doctor."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envault.doctor import DoctorManager, DoctorIssue, DoctorReport
from envault.storage import StorageManager


@pytest.fixture
def tmp_doctor(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    storage = StorageManager(config_dir=str(tmp_path / ".envault"))
    manager = DoctorManager(storage=storage)
    return manager, tmp_path


def test_doctor_issue_str_error():
    issue = DoctorIssue("error", "something broke")
    assert "ERROR" in str(issue)
    assert "something broke" in str(issue)
    assert "✗" in str(issue)


def test_doctor_issue_str_warning():
    issue = DoctorIssue("warning", "might be a problem")
    assert "WARNING" in str(issue)
    assert "⚠" in str(issue)


def test_doctor_report_ok_when_only_info():
    report = DoctorReport(issues=[DoctorIssue("info", "all good")])
    assert report.ok is True
    assert report.has_errors is False
    assert report.has_warnings is False


def test_doctor_report_not_ok_with_error():
    report = DoctorReport(issues=[DoctorIssue("error", "bad")])
    assert report.ok is False
    assert report.has_errors is True


def test_check_missing_key_returns_error(tmp_doctor):
    manager, _ = tmp_doctor
    report = manager.check("myproject")
    levels = [i.level for i in report.issues]
    assert "error" in levels
    messages = " ".join(i.message for i in report.issues)
    assert "myproject" in messages


def test_check_with_key_and_env_file(tmp_doctor):
    manager, tmp_path = tmp_doctor
    manager.storage.save_project_key("myproject", b"x" * 32)
    env = tmp_path / ".env"
    env.write_text("KEY=value\n")
    report = manager.check("myproject", env_file=str(env))
    assert not report.has_errors


def test_check_empty_env_file_gives_info(tmp_doctor):
    manager, tmp_path = tmp_doctor
    manager.storage.save_project_key("proj", b"k" * 32)
    env = tmp_path / ".env"
    env.write_text("")
    report = manager.check("proj", env_file=str(env))
    messages = " ".join(i.message for i in report.issues)
    assert "empty" in messages.lower()


def test_check_no_vault_file_gives_info(tmp_doctor):
    manager, tmp_path = tmp_doctor
    manager.storage.save_project_key("proj", b"k" * 32)
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    report = manager.check("proj", env_file=str(env))
    messages = " ".join(i.message for i in report.issues)
    assert "vault" in messages.lower()


def test_check_healthy_project_has_info_ok(tmp_doctor):
    manager, tmp_path = tmp_doctor
    manager.storage.save_project_key("proj", b"k" * 32)
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    vault = tmp_path / ".env.vault"
    vault.write_bytes(b"data")
    report = manager.check("proj", env_file=str(env))
    assert not report.has_errors
    assert not report.has_warnings
    assert report.ok
