"""CLI commands for env value truncation display."""
import click
from pathlib import Path
from envault.env_truncate import TruncateManager, TruncateError


@click.group("truncate")
def truncate_group() -> None:
    """Truncate long env values for display."""


@truncate_group.command("show")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--max-length", "-m", default=40, show_default=True, help="Maximum value length before truncation.")
@click.option("--summary", "show_summary", is_flag=True, default=False, help="Print summary line at the end.")
def show_cmd(env_file: Path, max_length: int, show_summary: bool) -> None:
    """Display env file with long values truncated."""
    try:
        manager = TruncateManager(max_length=max_length)
        result = manager.truncate(env_file, max_length=max_length)
    except TruncateError as exc:
        raise click.ClickException(str(exc))

    click.echo(result.as_text())
    if show_summary:
        click.echo()
        click.echo(result.summary())
    if result.changed:
        raise SystemExit(0)
