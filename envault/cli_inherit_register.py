"""Register the inherit command group with the main CLI."""
from __future__ import annotations

from envault.cli_inherit import inherit_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    """Attach the inherit command group to *cli*.

    Parameters
    ----------
    cli:
        The root Click group (or any object exposing ``add_command``) to
        which the ``inherit`` sub-group will be attached.

    Raises
    ------
    AttributeError
        If *cli* does not expose an ``add_command`` method.
    """
    if not hasattr(cli, "add_command"):
        raise AttributeError(
            f"Expected a Click group with 'add_command', got {type(cli).__name__!r}"
        )
    cli.add_command(inherit_group)  # type: ignore[attr-defined]
