"""CLI commands for searching vault entries."""

from __future__ import annotations

import click

from envault.storage import StorageManager
from envault.vault import VaultManager
from envault.search import SearchManager


@click.group()
def search_group() -> None:
    """Search and inspect vault entries."""


@search_group.command("search")
@click.argument("project")
@click.argument("pattern")
@click.option("--config-dir", default=None, help="Override config directory.")
@click.option("--password", default=None, help="Vault password.")
@click.option("--regex", "use_regex", is_flag=True, default=False, help="Use regex instead of glob.")
@click.option("--keys-only", is_flag=True, default=False, help="Print only matching key names.")
def search_cmd(project: str, pattern: str, config_dir: str | None, password: str | None, use_regex: bool, keys_only: bool) -> None:
    """Search PROJECT vault for variables matching PATTERN."""
    storage = StorageManager(config_dir=config_dir)
    vault = VaultManager(storage=storage)
    manager = SearchManager(vault=vault)

    results = manager.search(
        project,
        pattern,
        password=password,
        use_regex=use_regex,
        keys_only=keys_only,
    )

    if not results:
        click.echo("No matching variables found.")
        return

    for var_key, value in sorted(results.items()):
        if keys_only:
            click.echo(var_key)
        else:
            click.echo(f"{var_key}={value}")


@search_group.command("keys")
@click.argument("project")
@click.option("--config-dir", default=None, help="Override config directory.")
@click.option("--password", default=None, help="Vault password.")
def keys_cmd(project: str, config_dir: str | None, password: str | None) -> None:
    """List all variable names stored in PROJECT vault."""
    storage = StorageManager(config_dir=config_dir)
    vault = VaultManager(storage=storage)
    manager = SearchManager(vault=vault)

    keys = manager.list_keys(project, password=password)
    for k in keys:
        click.echo(k)
