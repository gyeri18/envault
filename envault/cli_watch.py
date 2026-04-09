"""CLI commands for the watch feature."""

from __future__ import annotations

from pathlib import Path

import click

from envault.audit import AuditLog
from envault.vault import VaultManager
from envault.watch import WatchEvent, WatchManager


@click.group("watch")
def watch_group() -> None:
    """Watch an .env file and react to changes."""


@watch_group.command("start")
@click.argument("project")
@click.option("--env-file", default=".env", show_default=True, help="Path to the .env file.")
@click.option("--config-dir", default=None, help="Override config directory.")
@click.option("--interval", default=2.0, show_default=True, help="Poll interval in seconds.")
@click.option("--password", default=None, help="Decryption password (if key-derived).")
def start_cmd(
    project: str,
    env_file: str,
    config_dir: str | None,
    interval: float,
    password: str | None,
) -> None:
    """Watch ENV_FILE and re-lock the vault whenever it changes."""
    env_path = Path(env_file)
    audit = AuditLog(config_dir=config_dir)
    vault = VaultManager(config_dir=config_dir)

    click.echo(f"Watching {env_path} for project '{project}' (interval={interval}s). Ctrl-C to stop.")

    def on_change(event: WatchEvent) -> None:
        click.echo(f"  [watch] Change detected — re-locking vault for '{project}'.")
        try:
            vault.lock(project, str(env_path), password=password)
            audit.record(project, "watch_lock", {"file": str(env_path)})
            click.echo(f"  [watch] Vault locked successfully.")
        except Exception as exc:  # noqa: BLE001
            click.echo(f"  [watch] ERROR: {exc}", err=True)

    manager = WatchManager(env_path=env_path, interval=interval)
    manager.start(on_change)
