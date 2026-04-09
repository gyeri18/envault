"""CLI tests for the watch command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_watch import watch_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\n")
    return p


def test_watch_start_invokes_manager(runner: CliRunner, env_file: Path) -> None:
    """Ensure the start command constructs WatchManager and calls start."""
    mock_manager = MagicMock()

    with patch("envault.cli_watch.WatchManager", return_value=mock_manager) as MockWM, \
         patch("envault.cli_watch.VaultManager"), \
         patch("envault.cli_watch.AuditLog"):
        result = runner.invoke(
            watch_group,
            ["start", "myproject", "--env-file", str(env_file), "--interval", "0.1"],
        )

    assert result.exit_code == 0
    MockWM.assert_called_once_with(env_path=env_file, interval=0.1)
    mock_manager.start.assert_called_once()


def test_watch_start_shows_watching_message(runner: CliRunner, env_file: Path) -> None:
    with patch("envault.cli_watch.WatchManager") as MockWM, \
         patch("envault.cli_watch.VaultManager"), \
         patch("envault.cli_watch.AuditLog"):
        MockWM.return_value.start = MagicMock()  # no-op
        result = runner.invoke(
            watch_group,
            ["start", "demo", "--env-file", str(env_file)],
        )

    assert "Watching" in result.output
    assert "demo" in result.output


def test_watch_start_on_change_locks_vault(runner: CliRunner, env_file: Path) -> None:
    """Simulate on_change callback locking the vault."""
    captured_callback = {}

    def fake_start(on_change, **kwargs):
        captured_callback["fn"] = on_change

    mock_vault = MagicMock()
    mock_audit = MagicMock()

    with patch("envault.cli_watch.WatchManager") as MockWM, \
         patch("envault.cli_watch.VaultManager", return_value=mock_vault), \
         patch("envault.cli_watch.AuditLog", return_value=mock_audit):
        MockWM.return_value.start = fake_start
        runner.invoke(
            watch_group,
            ["start", "proj", "--env-file", str(env_file)],
        )

    from envault.watch import WatchEvent
    event = WatchEvent(path=env_file, old_hash="a", new_hash="b")
    captured_callback["fn"](event)

    mock_vault.lock.assert_called_once_with("proj", str(env_file), password=None)
    mock_audit.record.assert_called_once()
