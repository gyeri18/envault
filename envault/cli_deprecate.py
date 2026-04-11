"""CLI commands for managing deprecated .env keys."""
import click
from pathlib import Path

from envault.env_deprecate import DeprecateManager, DeprecateError


@click.group(name="deprecate")
def deprecate_group() -> None:
    """Manage deprecated environment variable keys."""


def _manager(config_dir: str) -> DeprecateManager:
    return DeprecateManager(config_dir=Path(config_dir))


@deprecate_group.command(name="mark")
@click.argument("key")
@click.option("--reason", required=True, help="Why the key is deprecated.")
@click.option("--replacement", default=None, help="Suggested replacement key.")
@click.option("--config-dir", default=".envault", show_default=True)
def mark_cmd(key: str, reason: str, replacement: str, config_dir: str) -> None:
    """Mark KEY as deprecated."""
    try:
        entry = _manager(config_dir).mark(key, reason, replacement)
        click.echo(f"Marked '{entry.key}' as deprecated.")
        if entry.replacement:
            click.echo(f"  Replacement: {entry.replacement}")
    except DeprecateError as exc:
        raise click.ClickException(str(exc))


@deprecate_group.command(name="unmark")
@click.argument("key")
@click.option("--config-dir", default=".envault", show_default=True)
def unmark_cmd(key: str, config_dir: str) -> None:
    """Remove deprecation notice from KEY."""
    try:
        _manager(config_dir).unmark(key)
        click.echo(f"Removed deprecation for '{key}'.")
    except DeprecateError as exc:
        raise click.ClickException(str(exc))


@deprecate_group.command(name="list")
@click.option("--config-dir", default=".envault", show_default=True)
def list_cmd(config_dir: str) -> None:
    """List all deprecated keys."""
    report = _manager(config_dir).list_deprecated()
    if not report.entries:
        click.echo("No deprecated keys.")
        return
    for entry in report.entries:
        click.echo(f"  {entry}")


@deprecate_group.command(name="check")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--config-dir", default=".envault", show_default=True)
def check_cmd(env_file: str, config_dir: str) -> None:
    """Check ENV_FILE for deprecated keys."""
    lines = Path(env_file).read_text().splitlines()
    keys = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            keys.append(stripped.split("=", 1)[0].strip())
    report = _manager(config_dir).check(keys)
    if not report.entries:
        click.echo("No deprecated keys found.")
        return
    click.echo(f"Found {len(report.entries)} deprecated key(s):")
    for entry in report.entries:
        click.echo(f"  {entry}")
    raise SystemExit(1)
