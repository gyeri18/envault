"""CLI commands for importing env files into envault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.import_env import ImportManager
from envault.storage import StorageManager
from envault.vault import VaultManager


@click.group(name="import")
def import_group() -> None:
    """Import environment variables from external files."""


@import_group.command(name="file")
@click.argument("project")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "json", "shell"]),
    default="dotenv",
    show_default=True,
    help="Format of the source file.",
)
@click.option("--password", "-p", default=None, help="Encryption password (optional).")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing vault instead of merging.",
)
@click.option(
    "--config-dir",
    default=None,
    envvar="ENVAULT_CONFIG_DIR",
    help="Override config directory.",
)
def file_cmd(
    project: str,
    source: Path,
    fmt: str,
    password: str | None,
    overwrite: bool,
    config_dir: str | None,
) -> None:
    """Import SOURCE into PROJECT's vault.

    SOURCE can be a .env, JSON, or shell-export file.
    """
    storage = StorageManager(config_dir=config_dir)
    vault = VaultManager(storage=storage)
    manager = ImportManager(vault=vault)

    try:
        mapping = manager.import_file(
            source=source,
            project=project,
            fmt=fmt,
            password=password,
            overwrite=overwrite,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    click.echo(
        click.style("✔", fg="green")
        + f" Imported {len(mapping)} key(s) into project '{project}'."
    )
    for key in sorted(mapping):
        click.echo(f"  {key}")
