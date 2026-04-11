"""CLI commands for viewing per-key change history."""
import click
from pathlib import Path

from envault.env_history import HistoryManager


@click.group(name="history")
def history_group() -> None:
    """View change history for .env keys."""


@history_group.command(name="show")
@click.argument("project")
@click.option("--key", "-k", default=None, help="Filter by specific key name.")
@click.option(
    "--config-dir",
    default=str(Path.home() / ".envault"),
    show_default=True,
    help="Path to envault config directory.",
)
def show_cmd(project: str, key: str | None, config_dir: str) -> None:
    """Show history entries for PROJECT, optionally filtered by KEY."""
    manager = HistoryManager(config_dir=Path(config_dir), project=project)
    entries = manager.get_entries(key=key)
    if not entries:
        click.echo("No history found.")
        return
    for entry in entries:
        old_h = entry.old_value_hash or "(none)"
        new_h = entry.new_value_hash or "(none)"
        click.echo(
            f"{entry.timestamp}  {entry.action:<8}  {entry.key}  "
            f"{old_h} -> {new_h}"
        )


@history_group.command(name="clear")
@click.argument("project")
@click.option(
    "--config-dir",
    default=str(Path.home() / ".envault"),
    show_default=True,
    help="Path to envault config directory.",
)
@click.confirmation_option(prompt="Clear all history for this project?")
def clear_cmd(project: str, config_dir: str) -> None:
    """Clear all history entries for PROJECT."""
    manager = HistoryManager(config_dir=Path(config_dir), project=project)
    manager.clear()
    click.echo(f"History cleared for project '{project}'.")
