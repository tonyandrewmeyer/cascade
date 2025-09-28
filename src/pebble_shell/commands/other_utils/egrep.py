"""Implementation of EgrepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command
from pebble_shell.commands.builtin import GrepCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the text category.
class EgrepCommand(Command):
    """Search text using extended regular expressions."""

    name = "egrep"
    help = "Search text using extended regular expressions"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the egrep command."""
        # egrep is equivalent to grep -E
        grep_cmd = GrepCommand(self.shell)
        return grep_cmd.execute(client, ["-E", *args])
