"""CLI commands for managing env key defaults."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.env_default import DefaultError, DefaultManager


@click.group(name="default")
def default_group():
    """Manage default values for env keys."""


def _manager(config_dir: str) -> DefaultManager:
    return DefaultManager(config_dir=Path(config_dir) if config_dir else None)


@default_group.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--config-dir", default=None, hidden=True)
def set_cmd(key: str, value: str, config_dir: str):
    """Set a default VALUE for KEY."""
    try:
        entry = _manager(config_dir).set(key, value)
        click.echo(f"Default set: {entry}")
    except DefaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@default_group.command(name="remove")
@click.argument("key")
@click.option("--config-dir", default=None, hidden=True)
def remove_cmd(key: str, config_dir: str):
    """Remove the default for KEY."""
    try:
        _manager(config_dir).remove(key)
        click.echo(f"Default removed for key: {key}")
    except DefaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@default_group.command(name="list")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(config_dir: str):
    """List all registered defaults."""
    entries = _manager(config_dir).list_defaults()
    if not entries:
        click.echo("No defaults registered.")
        return
    for entry in entries:
        click.echo(str(entry))
