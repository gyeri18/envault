"""Registration helper for the required-keys CLI group."""
from __future__ import annotations

from envault.cli_required import required_group


def register(cli) -> None:  # type: ignore[type-arg]
    """Attach the 'required' command group to *cli*."""
    cli.add_command(required_group)
