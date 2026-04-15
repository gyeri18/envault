"""Registration helper so cli.py can attach the access command group."""
from envault.cli_access import access_group


def register(cli):
    """Attach the access sub-command group to *cli*."""
    cli.add_command(access_group, name="access")
