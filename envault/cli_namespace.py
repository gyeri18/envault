"""CLI commands for namespace management."""

from __future__ import annotations

import click

from envault.env_namespace import NamespaceError, NamespaceManager


@click.group(name="namespace", help="Manage key namespaces (prefix groups).")
def namespace_group() -> None:  # pragma: no cover
    pass


def _manager(config_dir: str) -> NamespaceManager:
    from pathlib import Path
    return NamespaceManager(Path(config_dir))


@namespace_group.command("create")
@click.argument("name")
@click.argument("prefix")
@click.option("--config-dir", default="~/.envault", show_default=True)
def create_cmd(name: str, prefix: str, config_dir: str) -> None:
    """Register a new namespace NAME mapped to PREFIX."""
    try:
        _manager(config_dir).create(name, prefix)
        click.echo(f"Namespace '{name}' created with prefix '{prefix}'.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_group.command("delete")
@click.argument("name")
@click.option("--config-dir", default="~/.envault", show_default=True)
def delete_cmd(name: str, config_dir: str) -> None:
    """Remove a namespace by NAME."""
    try:
        _manager(config_dir).delete(name)
        click.echo(f"Namespace '{name}' deleted.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_group.command("list")
@click.option("--config-dir", default="~/.envault", show_default=True)
def list_cmd(config_dir: str) -> None:
    """List all registered namespaces."""
    entries = _manager(config_dir).list_namespaces()
    if not entries:
        click.echo("No namespaces defined.")
        return
    for entry in entries:
        click.echo(f"{entry['name']:<20} {entry['prefix']}")
