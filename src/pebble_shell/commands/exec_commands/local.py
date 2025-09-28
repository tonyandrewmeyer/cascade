"""Run a local command."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LocalCommand(Command):
    """Run a local command."""

    name = "local"
    help = "Run a local command. Usage: local <command> [args...]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the local command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 1, "local <subcommand> [args...]"):
            return 1

        result = subprocess.run(  # noqa: S603
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            self.console.print(result.stdout, end="")
        if result.stderr:
            self.console.print(result.stderr, end="")
        return result.returncode
