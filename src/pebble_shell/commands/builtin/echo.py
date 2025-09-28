"""Print text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class EchoCommand(Command):
    """Print text."""

    name = "echo"
    help = "Display text"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute echo command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print()
            return 0

        output = " ".join(args)

        # Handle basic escape sequences
        output = output.replace("\\n", "\n")
        output = output.replace("\\t", "\t")
        output = output.replace("\\\\", "\\")

        self.console.print(output)
        return 0
