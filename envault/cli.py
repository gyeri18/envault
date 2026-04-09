"""Main CLI entry-point for envault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.cli_lint import lint_group
from envault.cli_profile import profile_group
from envault.cli_search import search_group
from envault.cli_snapshot import snapshot_group
from envault.cli_watch import watch_group
from envault.cli_doctor import doctor_group
from envault.export import ExportManager
from envault.vault import VaultManager


@click.group()
def cli() -> None:
    """envault — encrypted .env management."""


# Sub-command groups
cli.add_command(lint_group)
cli.add_command(profile_group)
cli.add_command(search_group)
cli.add_command(snapshot_group)
cli.add_command(watch_group)
cli.add_command(doctor_group)


@cli.command()
@click.argument("project")
@click.option("--config-dir", default=None)
@click.option("--password", default=None)
def init(project: str, config_dir: str | None, password: str | None) -> None:
    """Initialise a new project vault."""
    vault = VaultManager(config_dir=config_dir)
    key = vault.init_project(project, password=password)
    click.echo(f"Project '{project}' initialised.")
    if not password:
        click.echo(f"Key (keep safe): {key.hex()}")


@cli.command()
@click.argument("project")
@click.argument("env_file")
@click.option("--config-dir", default=None)
@click.option("--password", default=None)
def lock(project: str, env_file: str, config_dir: str | None, password: str | None) -> None:
    """Encrypt ENV_FILE into the vault."""
    vault = VaultManager(config_dir=config_dir)
    vault.lock(project, env_file, password=password)
    click.echo(f"Locked '{env_file}' for project '{project}'.")


@cli.command()
@click.argument("project")
@click.argument("env_file")
@click.option("--config-dir", default=None)
@click.option("--password", default=None)
def unlock(project: str, env_file: str, config_dir: str | None, password: str | None) -> None:
    """Decrypt the vault back to ENV_FILE."""
    vault = VaultManager(config_dir=config_dir)
    vault.unlock(project, env_file, password=password)
    click.echo(f"Unlocked vault for project '{project}' → {env_file}.")


@cli.command()
@click.argument("project")
@click.option("--format", "fmt", default="dotenv", show_default=True,
              type=click.Choice(["dotenv", "json", "shell"]))
@click.option("--output", default=None, help="Output file path (stdout if omitted).")
@click.option("--config-dir", default=None)
@click.option("--password", default=None)
def export(project: str, fmt: str, output: str | None, config_dir: str | None, password: str | None) -> None:
    """Export the vault contents in the chosen format."""
    manager = ExportManager(config_dir=config_dir)
    result = manager.export(project, fmt=fmt, password=password)
    if output:
        Path(output).write_text(result)
        click.echo(f"Exported to {output}.")
    else:
        click.echo(result)
