"""CLI commands for sorting .env file keys."""

from __future__ import annotations

from pathlib import Path

import click

from envault.env_sort import SortManager
from envault.exceptions import EnvaultError


@click.group("sort")
def sort_group() -> None:
    """Sort and organize .env file keys."""


@sort_group.command("keys")
@click.argument("env_file", default=".env", type=click.Path())
@click.option(
    "--group",
    "groups",
    multiple=True,
    metavar="PREFIX",
    help="Key prefix groups defining section order (repeatable).",
)
@click.option(
    "--reverse",
    is_flag=True,
    default=False,
    help="Sort in descending order.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print sorted output without modifying the file.",
)
def keys_cmd(
    env_file: str,
    groups: tuple,
    reverse: bool,
    dry_run: bool,
) -> None:
    """Sort keys in ENV_FILE alphabetically (or by prefix groups)."""
    manager = SortManager(Path(env_file))
    try:
        result = manager.sort(
            groups=list(groups) if groups else None,
            reverse=reverse,
            dry_run=dry_run,
        )
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc

    if dry_run:
        click.echo(result, nl=False)
        click.echo(click.style("[dry-run] File not modified.", fg="yellow"), err=True)
    else:
        click.echo(click.style(f"Sorted {env_file}", fg="green"))


@sort_group.command("check")
@click.argument("env_file", default=".env", type=click.Path())
def check_cmd(env_file: str) -> None:
    """Check whether ENV_FILE keys are already sorted."""
    manager = SortManager(Path(env_file))
    try:
        already = manager.is_sorted()
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc

    if already:
        click.echo(click.style(f"{env_file} keys are sorted.", fg="green"))
    else:
        click.echo(
            click.style(f"{env_file} keys are NOT sorted.", fg="red"), err=True
        )
        raise SystemExit(1)
