"""CLI commands for the envault doctor feature."""
import click

from envault.doctor import DoctorManager


@click.group(name="doctor")
def doctor_group():
    """Check the health of an envault project."""


@doctor_group.command(name="check")
@click.argument("project")
@click.option("--env-file", default=".env", show_default=True, help="Path to the .env file.")
@click.option("--config-dir", default=None, hidden=True, help="Override config directory (for testing).")
def check_cmd(project: str, env_file: str, config_dir: str | None):
    """Run health checks for PROJECT."""
    manager = DoctorManager(config_dir=config_dir)

    try:
        report = manager.check(project, env_file=env_file)
    except FileNotFoundError as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        raise SystemExit(2)

    for issue in report.issues:
        if issue.level == "error":
            click.secho(str(issue), fg="red")
        elif issue.level == "warning":
            click.secho(str(issue), fg="yellow")
        else:
            click.secho(str(issue), fg="cyan")

    if not report.issues:
        click.secho("No issues found.", fg="green")

    if report.has_errors:
        raise SystemExit(2)
    elif report.has_warnings:
        raise SystemExit(1)
