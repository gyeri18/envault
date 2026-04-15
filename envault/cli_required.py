"""CLI commands for managing required keys per project."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from envault.env_required import RequiredError, RequiredManager


@click.group(name="required")
def required_group() -> None:
    """Manage required keys for a project."""


def _manager(config_dir: Optional[str]) -> RequiredManager:
    return RequiredManager(config_dir=Path(config_dir) if config_dir else None)


@required_group.command(name="set")
@click.argument("project")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config-dir", default=None, hidden=True)
def set_cmd(project: str, keys: tuple, config_dir: Optional[str]) -> None:
    """Set required keys for PROJECT."""
    try:
        _manager(config_dir).set_required(project, list(keys))
        click.echo(f"Set {len(keys)} required key(s) for '{project}'.")
    except RequiredError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@required_group.command(name="list")
@click.argument("project")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(project: str, config_dir: Optional[str]) -> None:
    """List required keys for PROJECT."""
    keys = _manager(config_dir).get_required(project)
    if not keys:
        click.echo(f"No required keys defined for '{project}'.")
        return
    for key in keys:
        click.echo(key)


@required_group.command(name="check")
@click.argument("project")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--config-dir", default=None, hidden=True)
def check_cmd(project: str, env_file: Path, config_dir: Optional[str]) -> None:
    """Check that ENV_FILE contains all required keys for PROJECT."""
    try:
        result = _manager(config_dir).check(project, env_file)
        click.echo(result.summary())
        if not result.ok:
            sys.exit(1)
    except RequiredError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@required_group.command(name="remove")
@click.argument("project")
@click.option("--config-dir", default=None, hidden=True)
def remove_cmd(project: str, config_dir: Optional[str]) -> None:
    """Remove required-keys definition for PROJECT."""
    removed = _manager(config_dir).remove_required(project)
    if removed:
        click.echo(f"Removed required-keys definition for '{project}'.")
    else:
        click.echo(f"No required-keys definition found for '{project}'.")
