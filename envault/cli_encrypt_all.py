"""CLI commands for bulk-encrypting .env files."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_encrypt_all import EncryptAllManager, EncryptAllError


@click.group("encrypt-all")
def encrypt_all_group() -> None:
    """Bulk-encrypt every .env file under a directory."""


@encrypt_all_group.command("run")
@click.argument("root", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--pattern", default="**/.env*", show_default=True,
              help="Glob pattern relative to ROOT.")
@click.option("--password", default=None, envvar="ENVAULT_PASSWORD",
              help="Optional password for key derivation.")
@click.option("--config-dir", default=None, type=click.Path(),
              help="Override envault config directory.")
@click.option("--include-locked", is_flag=True, default=False,
              help="Re-encrypt files that already have a .vault file.")
def run_cmd(
    root: str,
    pattern: str,
    password: str | None,
    config_dir: str | None,
    include_locked: bool,
) -> None:
    """Walk ROOT and encrypt every matching .env file."""
    cfg = Path(config_dir) if config_dir else None
    manager = EncryptAllManager(config_dir=cfg, password=password)

    try:
        result = manager.encrypt_all(
            root=Path(root),
            pattern=pattern,
            skip_already_locked=not include_locked,
        )
    except EncryptAllError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    for p in result.encrypted:
        click.echo(f"  [encrypted] {p}")
    for p in result.skipped:
        click.echo(f"  [skipped]   {p}")
    for p, reason in result.failed:
        click.echo(f"  [failed]    {p} — {reason}", err=True)

    click.echo("")
    click.echo(result.summary())

    if not result.ok:
        raise SystemExit(1)
