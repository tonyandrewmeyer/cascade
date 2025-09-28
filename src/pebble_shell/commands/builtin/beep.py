"""Implementation of BeepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class BeepCommand(Command):
    """Play a beep sound."""

    name = "beep"
    help = "Play a beep sound"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the beep command."""
        # Handle help flag
        if handle_help_flag(self, args):
            return 0
        print("\a", end="", flush=True)
        return 0
