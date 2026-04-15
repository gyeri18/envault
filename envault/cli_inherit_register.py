"""Register the inherit command group with the main CLI."""
from __future__ import annotations

from envault.cli_inherit import inherit_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    """Attach the inherit command group to *cli*."""
    cli.add_command(inherit_group)  # type: ignore[attr-defined]
