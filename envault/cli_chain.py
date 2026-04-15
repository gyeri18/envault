"""CLI commands for env-chain feature."""
from __future__ import annotations

from pathlib import Path

import click

from .env_chain import ChainManager, ChainError


@click.group("chain")
def chain_group() -> None:
    """Merge multiple .env files with override precedence."""


@chain_group.command("merge")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Write merged result to file.")
@click.option("--show-sources", is_flag=True, default=False, help="Show which file each key came from.")
def merge_cmd(files: tuple, output: str | None, show_sources: bool) -> None:
    """Merge FILES in order (later files override earlier ones)."""
    manager = ChainManager()
    try:
        result = manager.chain(list(files))
    except ChainError as exc:
        raise click.ClickException(str(exc)) from exc

    if show_sources:
        click.echo("Key sources:")
        for key, src in sorted(result.sources.items()):
            click.echo(f"  {key}  <-  {src}")
        click.echo()

    if output:
        dest = manager.write(result, output)
        click.echo(f"Merged {result.key_count} keys -> {dest}")
    else:
        for key, value in sorted(result.merged.items()):
            click.echo(f"{key}={value}")
