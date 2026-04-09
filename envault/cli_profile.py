"""CLI commands for profile management."""

from __future__ import annotations

import click

from envault.profile import ProfileManager, DEFAULT_PROFILE
from envault.exceptions import EnvaultError


@click.group(name="profile")
def profile_group() -> None:
    """Manage multiple named profiles per project."""


@profile_group.command(name="lock")
@click.argument("project")
@click.argument("env_file", default=".env")
@click.option("--profile", "-p", default=DEFAULT_PROFILE, show_default=True,
              help="Profile name (e.g. dev, staging, prod).")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None, hidden=True)
@click.option("--config-dir", default=None, hidden=True)
def lock_cmd(project: str, env_file: str, profile: str,
             password: str, config_dir: str) -> None:
    """Encrypt ENV_FILE into the named profile vault."""
    try:
        mgr = ProfileManager(project_name=project, config_dir=config_dir)
        vault_path = mgr.lock_profile(env_file=env_file, profile=profile, password=password)
        click.echo(f"Locked profile '{profile}' → {vault_path}")
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command(name="unlock")
@click.argument("project")
@click.option("--profile", "-p", default=DEFAULT_PROFILE, show_default=True,
              help="Profile name to decrypt.")
@click.option("--output", "-o", default=None, help="Destination path for decrypted file.")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None, hidden=True)
@click.option("--config-dir", default=None, hidden=True)
def unlock_cmd(project: str, profile: str, output: str,
               password: str, config_dir: str) -> None:
    """Decrypt a named profile vault."""
    try:
        mgr = ProfileManager(project_name=project, config_dir=config_dir)
        dest = mgr.unlock_profile(profile=profile, output_path=output, password=password)
        click.echo(f"Unlocked profile '{profile}' → {dest}")
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command(name="list")
@click.argument("project")
@click.option("--config-dir", default=None, hidden=True)
def list_cmd(project: str, config_dir: str) -> None:
    """List all profiles for PROJECT."""
    try:
        mgr = ProfileManager(project_name=project, config_dir=config_dir)
        profiles = mgr.list_profiles()
        if not profiles:
            click.echo("No profiles found.")
        else:
            for name in profiles:
                click.echo(name)
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command(name="delete")
@click.argument("project")
@click.argument("profile")
@click.option("--config-dir", default=None, hidden=True)
def delete_cmd(project: str, profile: str, config_dir: str) -> None:
    """Delete a named profile vault."""
    try:
        mgr = ProfileManager(project_name=project, config_dir=config_dir)
        mgr.delete_profile(profile)
        click.echo(f"Deleted profile '{profile}' from project '{project}'.")
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc
