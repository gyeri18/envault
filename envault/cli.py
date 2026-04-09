"""CLI entry-point for envault using Click."""

from pathlib import Path

import click

from envault.vault import VaultManager


@click.group()
@click.version_option()
def cli():
    """envault — encrypt and manage your .env files."""


@cli.command()
@click.argument("project")
@click.option("--password", "-p", default=None, help="Derive key from password instead of generating one.")
def init(project: str, password: str):
    """Initialise a new project and generate its encryption key."""
    vault = VaultManager()
    try:
        vault.init_project(project, password)
        click.echo(f"✔ Project '{project}' initialised.")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


@cli.command()
@click.argument("project")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--password", "-p", default=None, help="Password used to derive the encryption key.")
def lock(project: str, env_file: Path, password: str):
    """Encrypt ENV_FILE and save it as <env_file>.vault."""
    vault = VaultManager()
    try:
        vault_path = vault.lock(project, env_file, password)
        click.echo(f"✔ Locked → {vault_path}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


@cli.command()
@click.argument("project")
@click.argument("vault_file", type=click.Path(exists=True, path_type=Path))
@click.option("--password", "-p", default=None, help="Password used to derive the decryption key.")
def unlock(project: str, vault_file: Path, password: str):
    """Decrypt VAULT_FILE and restore the original .env file."""
    vault = VaultManager()
    try:
        env_path = vault.unlock(project, vault_file, password)
        click.echo(f"✔ Unlocked → {env_path}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    cli()
