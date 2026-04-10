"""CLI commands for the backup feature."""

from __future__ import annotations

from pathlib import Path

import click

from envault.env_backup import BackupManager
from envault.exceptions import EnvaultError


@click.group(name="backup")
def backup_group() -> None:
    """Manage automatic .env file backups."""


@backup_group.command(name="create")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--config-dir", default=None, hidden=True, type=click.Path(path_type=Path))
def create_cmd(env_file: Path, config_dir: Path | None) -> None:
    """Create a backup of ENV_FILE."""
    try:
        manager = BackupManager(config_dir=config_dir)
        dest = manager.create(env_file)
        click.echo(f"Backup created: {dest}")
    except EnvaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@backup_group.command(name="list")
@click.argument("env_file", type=click.Path(path_type=Path))
@click.option("--config-dir", default=None, hidden=True, type=click.Path(path_type=Path))
def list_cmd(env_file: Path, config_dir: Path | None) -> None:
    """List all backups for ENV_FILE."""
    manager = BackupManager(config_dir=config_dir)
    backups = manager.list_backups(env_file)
    if not backups:
        click.echo("No backups found.")
        return
    for b in backups:
        click.echo(str(b))


@backup_group.command(name="restore")
@click.argument("env_file", type=click.Path(path_type=Path))
@click.option("--backup", default=None, type=click.Path(path_type=Path), help="Specific backup to restore.")
@click.option("--config-dir", default=None, hidden=True, type=click.Path(path_type=Path))
def restore_cmd(env_file: Path, backup: Path | None, config_dir: Path | None) -> None:
    """Restore ENV_FILE from a backup (defaults to most recent)."""
    try:
        manager = BackupManager(config_dir=config_dir)
        restored = manager.restore(env_file, backup_path=backup)
        click.echo(f"Restored: {restored}")
    except EnvaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@backup_group.command(name="delete")
@click.argument("backup_file", type=click.Path(exists=True, path_type=Path))
@click.option("--config-dir", default=None, hidden=True, type=click.Path(path_type=Path))
def delete_cmd(backup_file: Path, config_dir: Path | None) -> None:
    """Delete a specific backup file."""
    try:
        manager = BackupManager(config_dir=config_dir)
        manager.delete(backup_file)
        click.echo(f"Deleted backup: {backup_file}")
    except EnvaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
