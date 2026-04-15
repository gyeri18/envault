"""CLI commands for env inheritance."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_inherit import InheritError, InheritManager


@click.group("inherit")
def inherit_group() -> None:
    """Inherit variables from a base .env into a child .env."""


@inherit_group.command("apply")
@click.argument("base", type=click.Path(exists=True, path_type=Path))
@click.argument("child", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite keys that already exist in the child file.",
)
@click.option(
    "--prefix",
    default=None,
    help="Prepend a prefix to all inherited keys.",
)
def apply_cmd(
    base: Path,
    child: Path,
    overwrite: bool,
    prefix: str | None,
) -> None:
    """Inherit variables from BASE into CHILD."""
    manager = InheritManager(base_path=base, child_path=child)
    try:
        result = manager.apply(overwrite=overwrite, prefix=prefix)
    except InheritError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(result.summary())
    if result.added:
        for key in result.added:
            click.echo(f"  + {key}")
    if result.skipped:
        for key in result.skipped:
            click.echo(f"  ~ {key} (skipped)")

    raise SystemExit(0 if result.changed else 0)
