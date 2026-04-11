"""CLI commands for managing environment variable groups."""
import click
from pathlib import Path

from envault.env_group import GroupManager, GroupError


@click.group("group")
def group_group() -> None:
    """Manage named groups of environment variable keys."""


def _manager(config_dir: str) -> GroupManager:
    return GroupManager(Path(config_dir))


@group_group.command("create")
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config-dir", default=".envault", show_default=True)
def create_cmd(name: str, keys: tuple, config_dir: str) -> None:
    """Create a new group NAME containing KEYS."""
    try:
        _manager(config_dir).create(name, list(keys))
        click.echo(f"Group '{name}' created with {len(keys)} key(s).")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_group.command("delete")
@click.argument("name")
@click.option("--config-dir", default=".envault", show_default=True)
def delete_cmd(name: str, config_dir: str) -> None:
    """Delete group NAME."""
    try:
        _manager(config_dir).delete(name)
        click.echo(f"Group '{name}' deleted.")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_group.command("list")
@click.option("--config-dir", default=".envault", show_default=True)
def list_cmd(config_dir: str) -> None:
    """List all groups."""
    groups = _manager(config_dir).list_groups()
    if not groups:
        click.echo("No groups defined.")
    else:
        for g in groups:
            click.echo(g)


@group_group.command("show")
@click.argument("name")
@click.option("--config-dir", default=".envault", show_default=True)
def show_cmd(name: str, config_dir: str) -> None:
    """Show keys in group NAME."""
    try:
        keys = _manager(config_dir).get(name)
        click.echo(f"Group '{name}' ({len(keys)} key(s)):")
        for k in keys:
            click.echo(f"  {k}")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_group.command("add-key")
@click.argument("name")
@click.argument("key")
@click.option("--config-dir", default=".envault", show_default=True)
def add_key_cmd(name: str, key: str, config_dir: str) -> None:
    """Add KEY to group NAME."""
    try:
        _manager(config_dir).add_key(name, key)
        click.echo(f"Key '{key}' added to group '{name}'.")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_group.command("remove-key")
@click.argument("name")
@click.argument("key")
@click.option("--config-dir", default=".envault", show_default=True)
def remove_key_cmd(name: str, key: str, config_dir: str) -> None:
    """Remove KEY from group NAME."""
    try:
        _manager(config_dir).remove_key(name, key)
        click.echo(f"Key '{key}' removed from group '{name}'.")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
