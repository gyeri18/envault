"""Tests for the AuditLog module."""

import json
import pytest
from pathlib import Path
from envault.audit import AuditLog


@pytest.fixture
def audit(tmp_path):
    return AuditLog(config_dir=str(tmp_path))


class TestAuditLog:
    def test_log_file_created_on_record(self, audit, tmp_path):
        audit.record("myproject", "lock")
        assert (tmp_path / "audit.log").exists()

    def test_record_writes_valid_json(self, audit, tmp_path):
        audit.record("myproject", "lock", "encrypted .env")
        lines = (tmp_path / "audit.log").read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["project"] == "myproject"
        assert entry["action"] == "lock"
        assert entry["detail"] == "encrypted .env"
        assert "timestamp" in entry

    def test_get_entries_returns_all(self, audit):
        audit.record("proj_a", "init")
        audit.record("proj_b", "lock")
        audit.record("proj_a", "unlock")
        entries = audit.get_entries()
        assert len(entries) == 3

    def test_get_entries_filtered_by_project(self, audit):
        audit.record("proj_a", "init")
        audit.record("proj_b", "lock")
        audit.record("proj_a", "unlock")
        entries = audit.get_entries(project="proj_a")
        assert len(entries) == 2
        assert all(e["project"] == "proj_a" for e in entries)

    def test_get_entries_respects_limit(self, audit):
        for i in range(10):
            audit.record("proj", "lock", str(i))
        entries = audit.get_entries(limit=5)
        assert len(entries) == 5
        # Should return the most recent 5
        assert entries[-1]["detail"] == "9"

    def test_get_entries_empty_when_no_log(self, audit):
        entries = audit.get_entries()
        assert entries == []

    def test_clear_all_entries(self, audit):
        audit.record("proj_a", "init")
        audit.record("proj_b", "lock")
        removed = audit.clear()
        assert removed == 2
        assert audit.get_entries() == []

    def test_clear_by_project(self, audit):
        audit.record("proj_a", "init")
        audit.record("proj_b", "lock")
        audit.record("proj_a", "unlock")
        removed = audit.clear(project="proj_a")
        assert removed == 2
        remaining = audit.get_entries()
        assert len(remaining) == 1
        assert remaining[0]["project"] == "proj_b"

    def test_clear_nonexistent_log(self, audit):
        removed = audit.clear()
        assert removed == 0
