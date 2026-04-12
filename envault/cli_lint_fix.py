"""CLI commands for auto-fixing lint issues in .env files."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_lint_fix import LintFixError, LintFixManager


@click.group(name="lint-fix")
def lint_fix_group() -> None:
    """Auto-fix common .env lint issues."""


@lint_fix_group.command(name="run")
@click.argument("env_file", default=".env", type=click.Path())
@click.option("--no-dedup", is_flag=True, default=False, help="Skip duplicate key removal.")
@click.option("--no-strip", is_flag=True, default=False, help="Skip whitespace stripping.")
@click.option("--no-blank-collapse", is_flag=True, default=False,
              help="Skip blank-line collapsing.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would change without writing.")
def run_cmd(
    env_file: str,
    no_dedup: bool,
    no_strip: bool,
    no_blank_collapse: bool,
    dry_run: bool,
) -> None:
    """Apply automatic fixes to ENV_FILE."""
    path = Path(env_file)
    manager = LintFixManager(path)

    try:
        if dry_run:
            # Read a temporary copy
            import tempfile, shutil
            with tempfile.NamedTemporaryFile(delete=False, suffix=".env") as tmp:
                tmp_path = Path(tmp.name)
            shutil.copy2(path, tmp_path)
            tmp_manager = LintFixManager(tmp_path)
            result = tmp_manager.fix(
                remove_duplicates=not no_dedup,
                strip_whitespace=not no_strip,
                remove_blank_runs=not no_blank_collapse,
            )
            tmp_path.unlink(missing_ok=True)
            click.echo("[dry-run] " + result.summary())
        else:
            result = manager.fix(
                remove_duplicates=not no_dedup,
                strip_whitespace=not no_strip,
                remove_blank_runs=not no_blank_collapse,
            )
            click.echo(result.summary())
    except LintFixError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
