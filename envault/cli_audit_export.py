"""CLI commands for exporting the audit log."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from envault.env_audit_export import AuditExportManager, AuditExportError


@click.group("audit-export")
def audit_export_group() -> None:
    """Export the envault audit log."""


@audit_export_group.command("run")
@click.option(
    "--format", "fmt",
    type=click.Choice(["json", "csv", "text"]),
    default="json",
    show_default=True,
    help="Output format.",
)
@click.option("--project", default=None, help="Filter by project name.")
@click.option("--limit", default=None, type=int, help="Maximum number of entries (newest).")
@click.option("--output", "out_path", default=None, type=click.Path(), help="Write to file instead of stdout.")
@click.option("--config-dir", default=None, type=click.Path(), help="Custom config directory.")
def run_cmd(
    fmt: str,
    project: Optional[str],
    limit: Optional[int],
    out_path: Optional[str],
    config_dir: Optional[str],
) -> None:
    """Export audit log entries."""
    cfg = Path(config_dir) if config_dir else None
    manager = AuditExportManager(config_dir=cfg)
    try:
        result = manager.export(fmt=fmt, project=project, limit=limit)
    except AuditExportError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if out_path:
        dest = Path(out_path)
        result.write(dest)
        click.echo(f"Exported {result.entry_count} entries to {dest} ({fmt})")
    else:
        click.echo(result.output)
