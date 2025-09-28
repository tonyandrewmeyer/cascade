"""Implementation of GetoptCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Move this to the System category.
class GetoptCommand(Command):
    """Parse command line options."""

    name = "getopt"
    help = "Parse command line options"
    category = "System"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the getopt command."""
        return self._execute_getopt(client, args)

    def _execute_getopt(self, client: ClientType, args: list[str]) -> int:
        import getopt as getopt_module

        if len(args) < 2:
            self.console.print("Usage: getopt optstring parameters")
            return 1

        optstring = args[0]
        parameters = args[1:]

        try:
            opts, remaining = getopt_module.getopt(parameters, optstring)
            for opt, arg in opts:
                self.console.print(f"{opt} {arg}" if arg else opt, end=" ")
            self.console.print("--", end="")
            for param in remaining:
                self.console.print(f" {param}", end="")
            self.console.print()
        except getopt_module.GetoptError as e:
            self.console.print(f"getopt: {e}")
            return 1

        return 0
