"""CLI commands for comparing .env files."""
import click
from pathlib import Path

from envault.env_compare import CompareManager
from envault.exceptions import EnvaultError


@click.group(name="compare")
def compare_group() -> None:
    """Compare two .env files and show differences."""


@compare_group.command(name="files")
@click.argument("file_a", type=click.Path(exists=True, path_type=Path))
@click.argument("file_b", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--redact",
    is_flag=True,
    default=False,
    help="Redact values in output.",
)
@click.option(
    "--exit-code",
    is_flag=True,
    default=False,
    help="Exit with code 1 if differences are found.",
)
def files_cmd(file_a: Path, file_b: Path, redact: bool, exit_code: bool) -> None:
    """Compare FILE_A and FILE_B and print differences."""
    try:
        manager = CompareManager(redact=redact)
        result = manager.compare_files(file_a, file_b)
    except EnvaultError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Comparing {file_a} <-> {file_b}")
    if result.has_differences:
        click.echo(result.summary())
        click.echo(
            f"\nSummary: {len(result.only_in_a)} removed, "
            f"{len(result.only_in_b)} added, "
            f"{len(result.changed)} changed, "
            f"{len(result.unchanged)} unchanged."
        )
        if exit_code:
            raise SystemExit(1)
    else:
        click.echo("Files are identical.")
