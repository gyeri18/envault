"""Tests for AuditExportManager."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.env_audit_export import AuditExportManager, AuditExportError


@pytest.fixture()
def manager(tmp_path: Path) -> AuditExportManager:
    mgr = AuditExportManager(config_dir=tmp_path)
    # Seed a few audit entries directly via AuditLog
    from envault.audit import AuditLog
    log = AuditLog(config_dir=tmp_path)
    log.record(action="lock", project="alpha", detail="locked")
    log.record(action="unlock", project="alpha", detail="unlocked")
    log.record(action="lock", project="beta", detail="locked")
    return mgr


def test_export_json_format(manager: AuditExportManager) -> None:
    result = manager.export(fmt="json")
    assert result.format == "json"
    assert result.entry_count == 3
    parsed = json.loads(result.output)
    assert isinstance(parsed, list)
    assert len(parsed) == 3


def test_export_csv_format(manager: AuditExportManager) -> None:
    result = manager.export(fmt="csv")
    assert result.format == "csv"
    lines = result.output.strip().splitlines()
    # header + 3 data rows
    assert len(lines) == 4
    assert "action" in lines[0]


def test_export_text_format(manager: AuditExportManager) -> None:
    result = manager.export(fmt="text")
    assert result.format == "text"
    lines = result.output.strip().splitlines()
    assert len(lines) == 3
    assert "lock" in lines[0]


def test_export_filters_by_project(manager: AuditExportManager) -> None:
    result = manager.export(fmt="json", project="beta")
    assert result.entry_count == 1
    data = json.loads(result.output)
    assert data[0]["project"] == "beta"


def test_export_limit_returns_newest(manager: AuditExportManager) -> None:
    result = manager.export(fmt="json", limit=2)
    assert result.entry_count == 2


def test_export_unsupported_format_raises(manager: AuditExportManager) -> None:
    with pytest.raises(AuditExportError, match="Unsupported format"):
        manager.export(fmt="xml")  # type: ignore[arg-type]


def test_export_empty_log_returns_empty(tmp_path: Path) -> None:
    mgr = AuditExportManager(config_dir=tmp_path)
    result = mgr.export(fmt="json")
    assert result.entry_count == 0
    assert json.loads(result.output) == []


def test_export_write_to_file(manager: AuditExportManager, tmp_path: Path) -> None:
    result = manager.export(fmt="text")
    dest = tmp_path / "audit.txt"
    result.write(dest)
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == result.output
