"""CLI entry points for envault."""

import click
from pathlib import Path

from envault.vault import VaultManager
from envault.storage import StorageManager
from envault.export import ExportManager
from envault.exceptions import EnvaultError


@click.group()
def cli():
    """envault — encrypt and manage your .env files."""


@cli.command()
@click.argument("project")
@click.option("--env-file", default=".env", help="Path to the .env file.")
@click.option("--password", default=None, help="Optional password for key derivation.")
@click.option("--config-dir", default=None, hidden=True)
def init(project, env_file, password, config_dir):
    """Initialise a project and generate its encryption key."""
    try:
        storage = StorageManager(config_dir=config_dir)
        vault = VaultManager(storage=storage)
        vault.init_project(project, password=password)
        click.echo(f"Project '{project}' initialised.")
    except EnvaultError as exc:
        raise click.ClickException(str(exc))


@cli.command()
@click.argument("project")
@click.option("--env-file", default=".env", help="Path to the .env file.")
@click.option("--password", default=None, help="Password used during init.")
@click.option("--config-dir", default=None, hidden=True)
def lock(project, env_file, password, config_dir):
    """Encrypt the .env file into a vault."""
    try:
        storage = StorageManager(config_dir=config_dir)
        vault = VaultManager(storage=storage)
        vault.lock(project, env_path=Path(env_file), password=password)
        click.echo(f"Vault locked for project '{project}'.")
    except EnvaultError as exc:
        raise click.ClickException(str(exc))


@cli.command()
@click.argument("project")
@click.option("--password", default=None, help="Password used during init.")
@click.option("--config-dir", default=None, hidden=True)
def unlock(project, password, config_dir):
    """Decrypt the vault back to a .env file."""
    try:
        storage = StorageManager(config_dir=config_dir)
        vault = VaultManager(storage=storage)
        out = vault.unlock(project, password=password)
        click.echo(f"Vault unlocked → {out}")
    except EnvaultError as exc:
        raise click.ClickException(str(exc))


@cli.command(name="export")
@click.argument("project")
@click.option("--format", "fmt", default="dotenv", show_default=True,
              type=click.Choice(["dotenv", "json", "shell"]), help="Output format.")
@click.option("--output", default=None, help="Write output to this file instead of stdout.")
@click.option("--password", default=None, help="Password used during init.")
@click.option("--config-dir", default=None, hidden=True)
def export(project, fmt, output, password, config_dir):
    """Export decrypted env variables in a chosen format."""
    try:
        storage = StorageManager(config_dir=config_dir)
        vault = VaultManager(storage=storage)
        manager = ExportManager(vault=vault)
        out_path = Path(output) if output else None
        result = manager.export(project, fmt=fmt, password=password, output_path=out_path)
        if not output:
            click.echo(result, nl=False)
        else:
            click.echo(f"Exported to {output}")
    except EnvaultError as exc:
        raise click.ClickException(str(exc))
