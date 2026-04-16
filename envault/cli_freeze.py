"""CLI commands for freeze/unfreeze env keys."""
import click
from envault.env_freeze import FreezeManager, FreezeError


@click.group("freeze")
def freeze_group() -> None:
    """Freeze keys to prevent modification."""


def _manager(config_dir) -> FreezeManager:
    return FreezeManager(config_dir=config_dir) if config_dir else FreezeManager()


@freeze_group.command("mark")
@click.argument("key")
@click.option("--reason", default="", help="Reason for freezing.")
@click.option("--config-dir", default=None, hidden=True)
def mark_cmd(key: str, reason: str, config_dir) -> None:
    """Freeze a key."""
    try:
        _manager(config_dir).freeze(key, reason=reason)
        click.echo(f"Key '{key}' frozen.")
    except FreezeError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@freeze_group.command("unmark")
@click.argument("key")
@click.option("--config-dir", default=None, hidden=True)
def unmark_cmd(key: str, config_dir) -> None:
    """Unfreeze a key."""
    try:
        _manager(config_dir).unfreeze(key)
        click.echo(f"Key '{key}' unfrozen.")
    except FreezeError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@freeze_group.command("list")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(config_dir) -> None:
    """List all frozen keys."""
    entries = _manager(config_dir).list_frozen()
    if not entries:
        click.echo("No frozen keys.")
        return
    for e in entries:
        reason = f"  # {e['reason']}" if e["reason"] else ""
        click.echo(f"{e['key']}{reason}")
