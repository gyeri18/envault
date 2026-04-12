"""CLI commands for secret detection in .env files."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.env_secret import SecretError, SecretManager


@click.group("secret")
def secret_group() -> None:
    """Detect secrets and high-entropy values in .env files."""


@secret_group.command("scan")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--entropy-threshold",
    default=3.8,
    show_default=True,
    type=float,
    help="Shannon entropy threshold above which a value is flagged.",
)
@click.option("--quiet", "-q", is_flag=True, help="Only print summary.")
def scan_cmd(env_file: Path, entropy_threshold: float, quiet: bool) -> None:
    """Scan ENV_FILE for potential secrets."""
    manager = SecretManager(entropy_threshold=entropy_threshold)
    try:
        result = manager.scan(env_file)
    except SecretError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not quiet:
        for finding in result.findings:
            click.echo(str(finding))

    click.echo(result.summary())
    sys.exit(0 if result.ok else 1)
