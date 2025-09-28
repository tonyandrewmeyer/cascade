"""Implementation of ReformineCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from pebble_shell.utils.command_helpers import safe_read_file

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the text category.
class ReformineCommand(Command):
    """Reformat text to specified width."""

    name = "reformine"
    help = "Reformat text to specified width"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the reformine command."""
        return self._execute_reformine(client, args)

    def _execute_reformine(self, client: ClientType, args: list[str]) -> int:
        import textwrap

        width = 80
        if args and args[0].isdigit():
            width = int(args[0])
            args = args[1:]

        if args:
            for file_path in args:
                content = safe_read_file(client, file_path, self.shell)
                if content is not None:
                    wrapped = textwrap.fill(content, width=width)
                    self.console.print(wrapped)
        else:
            # Read from stdin - not implemented in container environment
            self.console.print("reformine: stdin reading not implemented")
            return 1

        return 0
