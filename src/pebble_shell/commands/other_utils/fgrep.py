"""Implementation of FgrepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from pebble_shell.commands.builtin import GrepCommand

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the text category.
class FgrepCommand(Command):
    """Search text using fixed strings."""

    name = "fgrep"
    help = "Search text using fixed strings"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the fgrep command."""
        # fgrep is equivalent to grep -F
        grep_cmd = GrepCommand(self.shell)
        return grep_cmd.execute(client, ["-F", *args])
