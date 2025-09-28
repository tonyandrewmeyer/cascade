"""Implementation of ClearCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Move this to System category.
class ClearCommand(Command):
    """Clear the terminal screen."""

    name = "clear"
    help = "Clear the terminal screen"
    category = "System"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the clear command."""
        self.console.clear()
        return 0
