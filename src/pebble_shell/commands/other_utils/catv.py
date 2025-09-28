"""Implementation of CatvCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from pebble_shell.utils.command_helpers import safe_read_file

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in one of the file categories.
class CatvCommand(Command):
    """Display file contents with visible control characters."""

    name = "catv"
    help = "Display file contents with visible control characters"
    category = "File"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the catv command."""
        return self._execute_catv(client, args)

    def _execute_catv(self, client: ClientType, args: list[str]) -> int:
        if not args:
            self.console.print("Usage: catv [files...]")
            return 1

        for file_path in args:
            try:
                content = safe_read_file(client, file_path, self.shell)
                if content is not None:
                    # Show control characters visibly
                    visible = content.replace("\t", "^I").replace("\n", "$\n")
                    self.console.print(visible, end="")
            except Exception as e:  # noqa: PERF203  # needed for robust file processing
                self.console.print(f"catv: {file_path}: {e}")
                return 1

        return 0
