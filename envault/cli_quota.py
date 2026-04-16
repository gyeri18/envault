"""CLI commands for quota management."""
import click
from pathlib import Path
from envault.env_quota import QuotaManager, QuotaError


@click.group("quota")
def quota_group() -> None:
    """Manage per-project key quotas."""


def _manager(config_dir: Optional[str]) -> QuotaManager:
    from typing import Optional
    return QuotaManager(config_dir=Path(config_dir) if config_dir else None)


@quota_group.command("set")
@click.argument("project")
@click.argument("limit", type=int)
@click.option("--config-dir", default=None, hidden=True)
def set_cmd(project: str, limit: int, config_dir: str) -> None:
    """Set the maximum number of keys allowed for PROJECT."""
    try:
        QuotaManager(config_dir=Path(config_dir) if config_dir else None).set_quota(project, limit)
        click.echo(f"Quota for '{project}' set to {limit} keys.")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@quota_group.command("remove")
@click.argument("project")
@click.option("--config-dir", default=None, hidden=True)
def remove_cmd(project: str, config_dir: str) -> None:
    """Remove the quota for PROJECT."""
    try:
        QuotaManager(config_dir=Path(config_dir) if config_dir else None).remove_quota(project)
        click.echo(f"Quota for '{project}' removed.")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@quota_group.command("list")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(config_dir: str) -> None:
    """List all configured quotas."""
    quotas = QuotaManager(config_dir=Path(config_dir) if config_dir else None).list_quotas()
    if not quotas:
        click.echo("No quotas configured.")
        return
    for project, limit in sorted(quotas.items()):
        click.echo(f"{project}: {limit}")


@quota_group.command("check")
@click.argument("project")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--config-dir", default=None, hidden=True)
def check_cmd(project: str, env_file: Path, config_dir: str) -> None:
    """Check whether PROJECT's env file exceeds its quota."""
    try:
        result = QuotaManager(config_dir=Path(config_dir) if config_dir else None).check(project, env_file)
        if result.ok:
            click.echo("OK: within quota.")
        else:
            click.echo(result.summary(), err=True)
            raise SystemExit(1)
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
