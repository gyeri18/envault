"""Tests for envault.env_expire."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.env_expire import ExpireError, ExpireManager, ExpiryEntry


@pytest.fixture()
def manager(tmp_path: Path) -> ExpireManager:
    return ExpireManager(tmp_path / ".envault")


def _future() -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat()


def _past() -> str:
    return (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()


def test_set_creates_entry(manager: ExpireManager) -> None:
    entry = manager.set("API_KEY", _future())
    assert entry.key == "API_KEY"


def test_set_stores_note(manager: ExpireManager) -> None:
    entry = manager.set("TOKEN", _future(), note="rotate quarterly")
    assert entry.note == "rotate quarterly"


def test_set_overwrites_existing(manager: ExpireManager) -> None:
    manager.set("API_KEY", _future())
    new_date = (datetime.now(tz=timezone.utc) + timedelta(days=60)).isoformat()
    manager.set("API_KEY", new_date)
    entries = manager.list_entries()
    assert len(entries) == 1
    assert entries[0].expires_at == new_date


def test_set_empty_key_raises(manager: ExpireManager) -> None:
    with pytest.raises(ExpireError, match="empty"):
        manager.set("", _future())


def test_set_invalid_date_raises(manager: ExpireManager) -> None:
    with pytest.raises(ExpireError, match="Invalid date"):
        manager.set("API_KEY", "not-a-date")


def test_remove_deletes_entry(manager: ExpireManager) -> None:
    manager.set("API_KEY", _future())
    manager.remove("API_KEY")
    assert manager.list_entries() == []


def test_remove_missing_key_raises(manager: ExpireManager) -> None:
    with pytest.raises(ExpireError, match="No expiry"):
        manager.remove("MISSING")


def test_list_returns_all_entries(manager: ExpireManager) -> None:
    manager.set("A", _future())
    manager.set("B", _future())
    keys = {e.key for e in manager.list_entries()}
    assert keys == {"A", "B"}


def test_check_returns_expired_entries(manager: ExpireManager) -> None:
    manager.set("OLD", _past())
    manager.set("NEW", _future())
    expired = manager.check()
    assert len(expired) == 1
    assert expired[0].key == "OLD"


def test_check_empty_when_none_expired(manager: ExpireManager) -> None:
    manager.set("NEW", _future())
    assert manager.check() == []


def test_entry_str_includes_key_and_date(manager: ExpireManager) -> None:
    date = _future()
    entry = manager.set("DB_PASS", date, note="monthly")
    text = str(entry)
    assert "DB_PASS" in text
    assert "monthly" in text


def test_persists_across_instances(tmp_path: Path) -> None:
    config = tmp_path / ".envault"
    ExpireManager(config).set("KEY", _future())
    entries = ExpireManager(config).list_entries()
    assert len(entries) == 1
    assert entries[0].key == "KEY"
