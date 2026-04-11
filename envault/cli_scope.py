"""CLI commands for env-scope management."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.env_scope import ScopeError, ScopeManager


@click.group("scope")
def scope_group() -> None:
    """Manage named key scopes."""


def _manager(config_dir: Optional[str]) -> ScopeManager:  # noqa: F821
    base = Path(config_dir) if config_dir else Path.home() / ".envault"
    return ScopeManager(base)


@scope_group.command("create")
@click.argument("scope")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config-dir", default=None, hidden=True)
def create_cmd(scope: str, keys: tuple, config_dir: str) -> None:
    """Create a scope with the specified KEYS."""
    try:
        _manager(config_dir).create(scope, list(keys))
        click.echo(f"Scope '{scope}' created with {len(keys)} key(s).")
    except ScopeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@scope_group.command("delete")
@click.argument("scope")
@click.option("--config-dir", default=None, hidden=True)
def delete_cmd(scope: str, config_dir: str) -> None:
    """Delete a named scope."""
    try:
        _manager(config_dir).delete(scope)
        click.echo(f"Scope '{scope}' deleted.")
    except ScopeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@scope_group.command("list")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(config_dir: str) -> None:
    """List all defined scopes."""
    scopes = _manager(config_dir).list_scopes()
    if not scopes:
        click.echo("No scopes defined.")
    else:
        for s in scopes:
            click.echo(s)


@scope_group.command("show")
@click.argument("scope")
@click.option("--config-dir", default=None, hidden=True)
def show_cmd(scope: str, config_dir: str) -> None:
    """Show keys belonging to SCOPE."""
    try:
        keys = _manager(config_dir).get(scope)
        click.echo(f"Scope '{scope}': {', '.join(keys)}")
    except ScopeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@scope_group.command("add-key")
@click.argument("scope")
@click.argument("key")
@click.option("--config-dir", default=None, hidden=True)
def add_key_cmd(scope: str, key: str, config_dir: str) -> None:
    """Add KEY to an existing SCOPE."""
    try:
        _manager(config_dir).add_key(scope, key)
        click.echo(f"Key '{key}' added to scope '{scope}'.")
    except ScopeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@scope_group.command("remove-key")
@click.argument("scope")
@click.argument("key")
@click.option("--config-dir", default=None, hidden=True)
def remove_key_cmd(scope: str, key: str, config_dir: str) -> None:
    """Remove KEY from SCOPE."""
    try:
        _manager(config_dir).remove_key(scope, key)
        click.echo(f"Key '{key}' removed from scope '{scope}'.")
    except ScopeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
