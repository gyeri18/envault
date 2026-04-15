"""CLI commands for env key expiry management."""
from __future__ import annotations

from pathlib import Path

import click

from .env_expire import ExpireError, ExpireManager


@click.group(name="expire")
def expire_group() -> None:
    """Manage expiry dates for environment variable keys."""


def _manager(config_dir: str) -> ExpireManager:
    return ExpireManager(Path(config_dir))


@expire_group.command("set")
@click.argument("key")
@click.argument("expires_at")
@click.option("--note", default="", help="Optional note about the expiry.")
@click.option("--config-dir", default=".envault", show_default=True)
def set_cmd(key: str, expires_at: str, note: str, config_dir: str) -> None:
    """Set an expiry date (ISO-8601) for KEY."""
    try:
        entry = _manager(config_dir).set(key, expires_at, note)
        click.echo(f"Set expiry for '{entry.key}': {entry.expires_at}")
    except ExpireError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expire_group.command("remove")
@click.argument("key")
@click.option("--config-dir", default=".envault", show_default=True)
def remove_cmd(key: str, config_dir: str) -> None:
    """Remove the expiry entry for KEY."""
    try:
        _manager(config_dir).remove(key)
        click.echo(f"Removed expiry for '{key}'.")
    except ExpireError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expire_group.command("list")
@click.option("--config-dir", default=".envault", show_default=True)
def list_cmd(config_dir: str) -> None:
    """List all keys with expiry dates."""
    entries = _manager(config_dir).list_entries()
    if not entries:
        click.echo("No expiry entries found.")
        return
    for entry in entries:
        status = " [EXPIRED]" if entry.is_expired() else ""
        click.echo(f"{entry}{status}")


@expire_group.command("check")
@click.option("--config-dir", default=".envault", show_default=True)
def check_cmd(config_dir: str) -> None:
    """Exit 1 and list keys that have expired."""
    expired = _manager(config_dir).check()
    if not expired:
        click.echo("No expired keys.")
        return
    click.echo(f"{len(expired)} expired key(s):")
    for entry in expired:
        click.echo(f"  {entry}")
    raise SystemExit(1)
