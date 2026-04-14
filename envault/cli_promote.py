"""CLI commands for env-promote feature."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from envault.env_promote import PromoteError, PromoteManager


@click.group("promote")
def promote_group() -> None:
    """Promote env variables between environment files."""


@promote_group.command("run")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("destination", type=click.Path(path_type=Path))
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Specific key(s) to promote. Repeatable. Defaults to all keys.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite keys that already exist in the destination.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be promoted without writing changes.",
)
def run_cmd(
    source: Path,
    destination: Path,
    keys: tuple,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Promote variables from SOURCE to DESTINATION."""
    manager = PromoteManager()
    selected = list(keys) if keys else None

    try:
        if dry_run:
            # Perform the operation on a temp copy for reporting only
            import tempfile, shutil
            with tempfile.NamedTemporaryFile(delete=False, suffix=".env") as tmp:
                tmp_path = Path(tmp.name)
            shutil.copy2(destination, tmp_path)
            result = manager.promote(source, tmp_path, keys=selected, overwrite=overwrite)
            tmp_path.unlink(missing_ok=True)
            click.echo(f"[dry-run] {result.summary()}")
            for k in result.promoted:
                click.echo(f"  + {k}")
            for k in result.overwritten:
                click.echo(f"  ~ {k}")
            for k in result.skipped:
                click.echo(f"  - {k} (skipped)")
        else:
            result = manager.promote(source, destination, keys=selected, overwrite=overwrite)
            click.echo(result.summary())
    except PromoteError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
