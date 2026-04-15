"""CLI commands for env variable interpolation."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_interpolate import InterpolateManager, InterpolateError


@click.group("interpolate")
def interpolate_group() -> None:
    """Expand ${VAR} references inside a .env file."""


@interpolate_group.command("show")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--context",
    "-c",
    multiple=True,
    metavar="KEY=VALUE",
    help="Extra KEY=VALUE pairs used as interpolation context.",
)
@click.option("--strict", is_flag=True, help="Exit 1 if any references are unresolved.")
def show_cmd(env_file: str, context: tuple, strict: bool) -> None:
    """Print the file with variable references expanded."""
    extra: dict = {}
    for item in context:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item}")
        k, _, v = item.partition("=")
        extra[k.strip()] = v.strip()

    manager = InterpolateManager(Path(env_file))
    try:
        result = manager.interpolate(context=extra)
    except InterpolateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    for key, value in result.pairs.items():
        click.echo(f"{key}={value}")

    if result.unresolved:
        click.echo(
            f"\nWarning: unresolved references: {', '.join(result.unresolved)}", err=True
        )
        if strict:
            raise SystemExit(1)
