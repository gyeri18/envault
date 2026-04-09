"""CLI commands for .env linting."""

from __future__ import annotations

from pathlib import Path

import click

from envault.lint import LintManager
from envault.exceptions import EnvaultError


@click.group(name="lint")
def lint_group() -> None:
    """Lint .env files for issues and best practices."""


@lint_group.command(name="check")
@click.argument("env_file", default=".env", type=click.Path())
@click.option("--strict", is_flag=True, default=False, help="Exit non-zero on warnings too.")
def check_cmd(env_file: str, strict: bool) -> None:
    """Check ENV_FILE for lint issues."""
    manager = LintManager()
    try:
        result = manager.lint(Path(env_file))
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.issues:
        click.echo(click.style(f"✔ {env_file}: no issues found.", fg="green"))
        return

    for issue in result.issues:
        color = {"error": "red", "warning": "yellow", "info": "cyan"}.get(issue.severity, "white")
        click.echo(click.style(str(issue), fg=color))

    total = len(result.issues)
    click.echo(f"\n{total} issue(s) found in {env_file}.")

    if result.has_errors or (strict and result.has_warnings):
        raise click.exceptions.Exit(1)
