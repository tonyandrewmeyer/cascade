"""Implementation of ResetCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the system category.
class ResetCommand(Command):
    """Reset terminal settings."""

    name = "reset"
    help = "Reset terminal settings"
    category = "System"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the reset command."""
        self.console.print("\033c", end="")  # Terminal reset escape sequence
        return 0
