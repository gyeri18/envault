"""Registration helper – attach diff-summary commands to the main CLI.

Import and call ``register(cli)`` from ``envault/cli.py`` to wire up the
``diff-summary`` command group without modifying the core CLI file.
"""
from __future__ import annotations

import click

from envault.cli_diff_summary import diff_summary_group


def register(cli: click.Group) -> None:
    """Add the diff-summary command group to *cli*."""
    cli.add_command(diff_summary_group)
