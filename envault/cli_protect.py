"""CLI commands for env key protection."""
import click
from pathlib import Path
from envault.env_protect import ProtectManager, ProtectError


@click.group("protect")
def protect_group():
    """Manage protected (immutable) env keys."""


def _manager(config_dir: str) -> ProtectManager:
    return ProtectManager(config_dir=Path(config_dir))


@protect_group.command("mark")
@click.argument("key")
@click.option("--reason", default="", help="Reason for protecting this key.")
@click.option("--config-dir", default=".envault", show_default=True)
def mark_cmd(key: str, reason: str, config_dir: str):
    """Mark a key as protected."""
    try:
        _manager(config_dir).protect(key, reason)
        click.echo(f"Key '{key}' is now protected.")
    except ProtectError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@protect_group.command("unmark")
@click.argument("key")
@click.option("--config-dir", default=".envault", show_default=True)
def unmark_cmd(key: str, config_dir: str):
    """Remove protection from a key."""
    try:
        _manager(config_dir).unprotect(key)
        click.echo(f"Key '{key}' is no longer protected.")
    except ProtectError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@protect_group.command("list")
@click.option("--config-dir", default=".envault", show_default=True)
def list_cmd(config_dir: str):
    """List all protected keys."""
    entries = _manager(config_dir).list_protected()
    if not entries:
        click.echo("No protected keys.")
        return
    for entry in entries:
        reason = f" — {entry['reason']}" if entry["reason"] else ""
        click.echo(f"{entry['key']}{reason}")


@protect_group.command("check")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config-dir", default=".envault", show_default=True)
def check_cmd(keys, config_dir: str):
    """Check whether given keys are protected."""
    violations = _manager(config_dir).check(list(keys))
    if not violations:
        click.echo("No violations.")
        return
    for v in violations:
        click.echo(f"PROTECTED  {v}", err=True)
    raise SystemExit(1)
