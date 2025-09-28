"""Implementation of InfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class InfoCommand(Command):
    """Command for displaying system and shell information."""
    name = "info"
    help = "Show system information"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the info command to display system information."""
        if handle_help_flag(self, args):
            return 0
        self.console.print("=== Cascade System Information ===")
        self.console.print()

        self.console.print("Shell Information:")
        self.console.print(f"  Current Directory: {self.shell.current_directory}")
        self.console.print()

        # TODO: We should add more things here!

        self.console.print("Use 'help' to see all shell features")
        return 0
