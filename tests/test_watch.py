"""Tests for envault.watch."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.watch import WatchEvent, WatchManager


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return p


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------


def test_watch_event_stores_fields(env_file: Path) -> None:
    event = WatchEvent(path=env_file, old_hash="aaa", new_hash="bbb")
    assert event.path == env_file
    assert event.old_hash == "aaa"
    assert event.new_hash == "bbb"
    assert event.timestamp <= time.time()


# ---------------------------------------------------------------------------
# WatchManager.current_hash
# ---------------------------------------------------------------------------


def test_current_hash_returns_string_for_existing_file(env_file: Path) -> None:
    manager = WatchManager(env_path=env_file)
    h = manager.current_hash()
    assert isinstance(h, str) and len(h) == 64


def test_current_hash_returns_none_for_missing_file(tmp_path: Path) -> None:
    manager = WatchManager(env_path=tmp_path / "missing.env")
    assert manager.current_hash() is None


def test_current_hash_changes_when_file_changes(env_file: Path) -> None:
    manager = WatchManager(env_path=env_file)
    h1 = manager.current_hash()
    env_file.write_text("KEY=changed\n")
    h2 = manager.current_hash()
    assert h1 != h2


# ---------------------------------------------------------------------------
# WatchManager.has_changed
# ---------------------------------------------------------------------------


def test_has_changed_false_on_first_call_if_stable(env_file: Path) -> None:
    manager = WatchManager(env_path=env_file)
    # Seed the last hash
    manager._last_hash = manager.current_hash()
    assert manager.has_changed() is False


def test_has_changed_true_after_modification(env_file: Path) -> None:
    manager = WatchManager(env_path=env_file)
    manager._last_hash = manager.current_hash()
    env_file.write_text("KEY=new_value\n")
    assert manager.has_changed() is True


# ---------------------------------------------------------------------------
# WatchManager.start (limited via max_events)
# ---------------------------------------------------------------------------


def test_start_fires_callback_on_change(env_file: Path) -> None:
    manager = WatchManager(env_path=env_file, interval=0.05)
    events: list[WatchEvent] = []

    def mutate_file() -> None:
        time.sleep(0.08)
        env_file.write_text("KEY=mutated\n")

    import threading
    threading.Thread(target=mutate_file, daemon=True).start()

    manager.start(on_change=events.append, max_events=1)

    assert len(events) == 1
    assert events[0].path == env_file


def test_stop_halts_loop(env_file: Path) -> None:
    manager = WatchManager(env_path=env_file, interval=0.05)

    import threading

    def stopper() -> None:
        time.sleep(0.12)
        manager.stop()

    threading.Thread(target=stopper, daemon=True).start()
    manager.start(on_change=lambda e: None, max_events=0)
    assert manager._running is False
