"""Implementation of PrintenvCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PrintenvCommand(Command):
    """Command for printing environment variables."""
    name = "printenv"
    help = "Print environment variables"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the printenv command to display environment variables."""
        if handle_help_flag(self, args):
            return 0

        try:
            if not args:
                # Print all environment variables
                for key, value in sorted(os.environ.items()):
                    self.console.print(f"{key}={value}")
            else:
                # Print specific variables
                exit_code = 0
                for var in args:
                    value = os.environ.get(var)
                    if value is not None:
                        self.console.print(value)
                    else:
                        exit_code = 1  # At least one variable was not found

                return exit_code

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"printenv: {e}"))
            return 1
