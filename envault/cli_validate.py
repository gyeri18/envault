"""CLI commands for .env schema validation."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_validate import ValidateManager


@click.group("validate")
def validate_group() -> None:
    """Validate .env files against a schema."""


@validate_group.command("check")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("schema_file", type=click.Path(exists=True, path_type=Path))
@click.option("--config-dir", default=None, hidden=True)
def check_cmd(env_file: Path, schema_file: Path, config_dir: str | None) -> None:
    """Validate ENV_FILE against SCHEMA_FILE."""
    manager = ValidateManager(config_dir=config_dir)
    result = manager.validate(env_file, schema_file)

    if not result.issues:
        click.secho("✔ All checks passed.", fg="green")
        return

    for issue in result.issues:
        color = "red" if issue.level == "error" else "yellow"
        click.secho(str(issue), fg=color)

    if result.ok:
        click.secho(f"\n{len(result.warnings())} warning(s).", fg="yellow")
    else:
        click.secho(
            f"\n{len(result.errors())} error(s), {len(result.warnings())} warning(s).",
            fg="red",
        )
        raise SystemExit(1)


@validate_group.command("generate-schema")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def generate_schema_cmd(env_file: Path, output: Path) -> None:
    """Generate a skeleton schema from an existing ENV_FILE."""
    lines = []
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.partition("=")[0].strip()
        lines.append(f"{key}  # type: str")
    output.write_text("\n".join(lines) + "\n")
    click.secho(f"Schema written to {output}", fg="green")
