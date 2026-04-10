"""CLI commands for managing env-key aliases."""
import click

from envault.env_alias import AliasManager
from envault.exceptions import EnvaultError


@click.group("alias")
def alias_group() -> None:
    """Manage short aliases for environment variable keys."""


@alias_group.command("add")
@click.argument("alias")
@click.argument("key")
@click.option("--config-dir", default="~/.envault", show_default=True)
def add_cmd(alias: str, key: str, config_dir: str) -> None:
    """Add ALIAS as a shorthand for KEY."""
    try:
        mgr = AliasManager(config_dir)
        mgr.add(alias, key)
        click.echo(f"Alias '{alias}' -> '{key}' added.")
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("remove")
@click.argument("alias")
@click.option("--config-dir", default="~/.envault", show_default=True)
def remove_cmd(alias: str, config_dir: str) -> None:
    """Remove an alias."""
    try:
        mgr = AliasManager(config_dir)
        mgr.remove(alias)
        click.echo(f"Alias '{alias}' removed.")
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("resolve")
@click.argument("alias")
@click.option("--config-dir", default="~/.envault", show_default=True)
def resolve_cmd(alias: str, config_dir: str) -> None:
    """Print the key that ALIAS points to."""
    try:
        mgr = AliasManager(config_dir)
        key = mgr.resolve(alias)
        click.echo(key)
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("list")
@click.option("--config-dir", default="~/.envault", show_default=True)
def list_cmd(config_dir: str) -> None:
    """List all registered aliases."""
    mgr = AliasManager(config_dir)
    entries = mgr.list_aliases()
    if not entries:
        click.echo("No aliases defined.")
        return
    for entry in entries:
        click.echo(f"{entry['alias']:20s} -> {entry['key']}")


@alias_group.command("rename")
@click.argument("old_alias")
@click.argument("new_alias")
@click.option("--config-dir", default="~/.envault", show_default=True)
def rename_cmd(old_alias: str, new_alias: str, config_dir: str) -> None:
    """Rename OLD_ALIAS to NEW_ALIAS."""
    try:
        mgr = AliasManager(config_dir)
        mgr.rename(old_alias, new_alias)
        click.echo(f"Alias '{old_alias}' renamed to '{new_alias}'.")
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc
