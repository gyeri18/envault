"""CLI commands for the diff-summary feature."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_diff_summary import DiffSummaryManager


@click.group(name="diff-summary")
def diff_summary_group() -> None:
    """Summarise differences between two .env files."""


@diff_summary_group.command(name="show")
@click.argument("base", type=click.Path(exists=True, dir_okay=False))
@click.argument("target", type=click.Path(exists=True, dir_okay=False))
@click.option("--show-unchanged", is_flag=True, default=False,
              help="Also print keys that are identical in both files.")
@click.option("--no-redact", is_flag=True, default=False,
              help="Show actual values instead of redacting them.")
def show_cmd(base: str, target: str, show_unchanged: bool, no_redact: bool) -> None:
    """Print a human-readable diff summary between BASE and TARGET."""
    manager = DiffSummaryManager(redact=not no_redact)
    summary = manager.summarise(Path(base), Path(target))

    if not summary.has_differences() and not show_unchanged:
        click.echo("No differences found.")
        return

    output = summary.render(show_unchanged=show_unchanged)
    click.echo(output)

    click.echo(
        f"\nSummary: {len(summary.added)} added, "
        f"{len(summary.removed)} removed, "
        f"{len(summary.changed)} changed, "
        f"{len(summary.unchanged)} unchanged."
    )

    if summary.has_differences():
        raise SystemExit(1)
