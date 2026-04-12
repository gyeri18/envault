"""CLI commands for masking sensitive .env values."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_mask import MaskError, MaskManager


@click.group("mask")
def mask_group() -> None:
    """Mask sensitive values in .env files."""


@mask_group.command("show")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--key", "-k", multiple=True, help="Explicitly mask this key.")
@click.option("--no-auto", is_flag=True, default=False, help="Disable auto-detection of sensitive keys.")
@click.option("--show-chars", default=4, show_default=True, help="Number of characters to reveal.")
def show_cmd(env_file: Path, key: tuple, no_auto: bool, show_chars: int) -> None:
    """Print .env file with sensitive values masked."""
    manager = MaskManager(show_chars=show_chars)
    try:
        result = manager.mask_file(
            env_file,
            keys=list(key) if key else None,
            auto_detect=not no_auto,
        )
    except MaskError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.as_text())
    if result.masked_keys:
        click.echo(
            click.style(
                f"\nMasked {len(result.masked_keys)} key(s): {', '.join(result.masked_keys)}",
                fg="yellow",
            ),
            err=True,
        )


@mask_group.command("list")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--no-auto", is_flag=True, default=False, help="Disable auto-detection.")
def list_cmd(env_file: Path, no_auto: bool) -> None:
    """List keys that would be masked."""
    manager = MaskManager()
    try:
        result = manager.mask_file(env_file, auto_detect=not no_auto)
    except MaskError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.masked_keys:
        click.echo("No sensitive keys detected.")
        return

    for k in result.masked_keys:
        click.echo(k)
