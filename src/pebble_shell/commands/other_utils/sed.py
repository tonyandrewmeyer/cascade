"""Implementation of SedCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the text category.
class SedCommand(Command):
    """Stream editor for filtering and transforming text."""

    name = "sed"
    help = "Stream editor for filtering and transforming text"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the sed command."""
        return self._execute_sed(client, args)

    def _execute_sed(self, client: ClientType, args: list[str]) -> int:
        if not args:
            self.console.print("Usage: sed [options] script [file...]")
            return 1

        # TODO: Implement this!
        return 1
