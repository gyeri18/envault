"""CLI commands for managing inline .env comments."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_comment import CommentError, CommentManager


@click.group("comment")
def comment_group() -> None:
    """Manage inline comments on .env keys."""


def _manager(env_file: str) -> CommentManager:
    return CommentManager(Path(env_file))


@comment_group.command("set")
@click.argument("env_file")
@click.argument("key")
@click.argument("comment")
def set_cmd(env_file: str, key: str, comment: str) -> None:
    """Add or replace the inline comment for KEY in ENV_FILE."""
    try:
        _manager(env_file).set(key, comment)
        click.echo(f"Comment set on '{key}'.")
    except CommentError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@comment_group.command("remove")
@click.argument("env_file")
@click.argument("key")
def remove_cmd(env_file: str, key: str) -> None:
    """Remove the inline comment from KEY in ENV_FILE."""
    try:
        _manager(env_file).remove(key)
        click.echo(f"Comment removed from '{key}'.")
    except CommentError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@comment_group.command("list")
@click.argument("env_file")
def list_cmd(env_file: str) -> None:
    """List all keys that have inline comments in ENV_FILE."""
    try:
        entries = _manager(env_file).list()
    except CommentError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not entries:
        click.echo("No inline comments found.")
        return
    for entry in entries:
        click.echo(str(entry))
