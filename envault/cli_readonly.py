"""CLI commands for managing read-only env keys."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from .env_readonly import ReadonlyError, ReadonlyManager


@click.group("readonly")
def readonly_group() -> None:
    """Mark env keys as read-only to prevent accidental changes."""


def _manager(config_dir: str) -> ReadonlyManager:
    return ReadonlyManager(config_dir=config_dir)


@readonly_group.command("mark")
@click.argument("key")
@click.option("--config-dir", default=".envault", show_default=True)
def mark_cmd(key: str, config_dir: str) -> None:
    """Mark KEY as read-only."""
    try:
        _manager(config_dir).mark(key)
        click.echo(f"Key '{key}' marked as read-only.")
    except ReadonlyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@readonly_group.command("unmark")
@click.argument("key")
@click.option("--config-dir", default=".envault", show_default=True)
def unmark_cmd(key: str, config_dir: str) -> None:
    """Remove read-only protection from KEY."""
    try:
        _manager(config_dir).unmark(key)
        click.echo(f"Key '{key}' is no longer read-only.")
    except ReadonlyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@readonly_group.command("list")
@click.option("--config-dir", default=".envault", show_default=True)
def list_cmd(config_dir: str) -> None:
    """List all read-only keys."""
    keys = _manager(config_dir).list_keys()
    if not keys:
        click.echo("No read-only keys defined.")
        return
    for key in keys:
        click.echo(key)


@readonly_group.command("check")
@click.argument("key")
@click.argument("value")
@click.argument("env_file", metavar="ENV_FILE")
@click.option("--config-dir", default=".envault", show_default=True)
def check_cmd(key: str, value: str, env_file: str, config_dir: str) -> None:
    """Check whether setting KEY=VALUE would violate a read-only constraint."""
    try:
        _manager(config_dir).check(key, value, Path(env_file))
        click.echo(f"OK: '{key}' can be set.")
    except ReadonlyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
