"""CLI commands for snapshot management."""

import click
from pathlib import Path

from envault.snapshot import SnapshotManager
from envault.vault import VaultManager
from envault.storage import StorageManager
from envault.exceptions import SnapshotError


@click.group(name="snapshot")
def snapshot_group():
    """Manage point-in-time snapshots of .env vaults."""


@snapshot_group.command(name="create")
@click.argument("project")
@click.option("--env-file", default=".env", show_default=True, help="Path to the .env file.")
@click.option("--label", default=None, help="Optional snapshot label (default: timestamp).")
@click.option("--password", default=None, hide_input=True, help="Vault password if applicable.")
@click.option("--config-dir", default=None, hidden=True)
def create_cmd(project, env_file, label, password, config_dir):
    """Create a snapshot of the current .env vault."""
    config_path = Path(config_dir) if config_dir else None
    storage = StorageManager(config_dir=config_path)
    vault = VaultManager(storage=storage)
    manager = SnapshotManager(vault=vault, config_dir=config_path)
    try:
        created_label = manager.create(project, Path(env_file), label=label, password=password)
        click.echo(f"Snapshot '{created_label}' created for project '{project}'.")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@snapshot_group.command(name="restore")
@click.argument("project")
@click.argument("label")
@click.option("--output", default=".env", show_default=True, help="Path to write restored .env.")
@click.option("--password", default=None, hide_input=True)
@click.option("--config-dir", default=None, hidden=True)
def restore_cmd(project, label, output, password, config_dir):
    """Restore a snapshot to a .env file."""
    config_path = Path(config_dir) if config_dir else None
    storage = StorageManager(config_dir=config_path)
    vault = VaultManager(storage=storage)
    manager = SnapshotManager(vault=vault, config_dir=config_path)
    try:
        manager.restore(project, label, Path(output), password=password)
        click.echo(f"Snapshot '{label}' restored to '{output}'.")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@snapshot_group.command(name="list")
@click.argument("project")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(project, config_dir):
    """List all snapshots for a project."""
    config_path = Path(config_dir) if config_dir else None
    storage = StorageManager(config_dir=config_path)
    vault = VaultManager(storage=storage)
    manager = SnapshotManager(vault=vault, config_dir=config_path)
    snapshots = manager.list_snapshots(project)
    if not snapshots:
        click.echo(f"No snapshots found for project '{project}'.")
        return
    for s in snapshots:
        click.echo(f"  [{s['created_at']}] {s['label']}  (source: {s['source']})")


@snapshot_group.command(name="delete")
@click.argument("project")
@click.argument("label")
@click.option("--config-dir", default=None, hidden=True)
def delete_cmd(project, label, config_dir):
    """Delete a named snapshot."""
    config_path = Path(config_dir) if config_dir else None
    storage = StorageManager(config_dir=config_path)
    vault = VaultManager(storage=storage)
    manager = SnapshotManager(vault=vault, config_dir=config_path)
    try:
        manager.delete(project, label)
        click.echo(f"Snapshot '{label}' deleted.")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
