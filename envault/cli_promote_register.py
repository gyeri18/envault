"""Register the promote command group with the main CLI."""
from __future__ import annotations

from envault.cli_promote import promote_group


def register(cli) -> None:  # type: ignore[type-arg]
    """Attach the promote command group to *cli*.

    Usage in envault/cli.py::

        from envault.cli_promote_register import register
        register(cli)
    """
    cli.add_command(promote_group)
