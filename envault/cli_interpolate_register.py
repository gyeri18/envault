"""Register the interpolate CLI group."""
from envault.cli_interpolate import interpolate_group


def register(cli) -> None:  # type: ignore[type-arg]
    """Attach the interpolate command group to *cli*."""
    cli.add_command(interpolate_group)
