"""Implementation of BracketTestCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class BracketTestCommand(Command):
    """The [ (bracket test) command."""

    name = "["
    help = "Evaluate conditional expressions (stub)"
    category = "Advanced Utilities"

    def execute(self, client: ops.pebble.Client, args: list[str]) -> int:
        """Execute bracket test command."""
        # TODO: Implement this!
        self.console.print(
            "[yellow][ command: stub implementation - not yet fully implemented[/yellow]"
        )
        return 0
