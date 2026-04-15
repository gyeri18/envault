"""CLI commands for env-key access control."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_access import AccessManager, AccessError


@click.group("access")
def access_group():
    """Manage role-based access to env keys."""


def _manager(config_dir: str) -> AccessManager:
    return AccessManager(config_dir=Path(config_dir) if config_dir else None)


@access_group.command("grant")
@click.argument("role")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config-dir", default=None, hidden=True)
def grant_cmd(role: str, keys: tuple, config_dir: str):
    """Grant ROLE access to one or more KEYS."""
    mgr = _manager(config_dir)
    try:
        entry = mgr.grant(role, list(keys))
        click.echo(f"Granted '{role}' access to: {', '.join(entry.keys)}")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("revoke")
@click.argument("role")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config-dir", default=None, hidden=True)
def revoke_cmd(role: str, keys: tuple, config_dir: str):
    """Revoke ROLE's access to one or more KEYS."""
    mgr = _manager(config_dir)
    try:
        entry = mgr.revoke(role, list(keys))
        remaining = ", ".join(entry.keys) if entry.keys else "(none)"
        click.echo(f"Remaining keys for '{role}': {remaining}")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("check")
@click.argument("role")
@click.argument("key")
@click.option("--config-dir", default=None, hidden=True)
def check_cmd(role: str, key: str, config_dir: str):
    """Check whether ROLE can access KEY (exits 0 = yes, 1 = no)."""
    mgr = _manager(config_dir)
    if mgr.can_access(role, key):
        click.echo(f"'{role}' can access '{key}'.")
    else:
        click.echo(f"'{role}' cannot access '{key}'.")
        raise SystemExit(1)


@access_group.command("list")
@click.option("--role", default=None, help="Filter by role.")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(role: str, config_dir: str):
    """List roles and their allowed keys."""
    mgr = _manager(config_dir)
    roles = [role] if role else mgr.list_roles()
    if not roles:
        click.echo("No roles defined.")
        return
    for r in roles:
        keys = mgr.allowed_keys(r)
        click.echo(f"{r}: {', '.join(keys) if keys else '(none)'}")


@access_group.command("delete")
@click.argument("role")
@click.option("--config-dir", default=None, hidden=True)
def delete_cmd(role: str, config_dir: str):
    """Delete a role and all its grants."""
    mgr = _manager(config_dir)
    try:
        mgr.delete_role(role)
        click.echo(f"Role '{role}' deleted.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
