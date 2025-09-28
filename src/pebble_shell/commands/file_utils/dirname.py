"""Implementation of DirnameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DirnameCommand(Command):
    """Implementation of dirname command."""

    name = "dirname"
    help = "Strip last component from file name"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Strip last component from file name.

Usage: dirname NAME...

Description:
    Print NAME with its trailing /component removed; if NAME contains
    no /, output '.' (meaning the current directory).

Examples:
    dirname /usr/bin/sort    # Output: /usr/bin
    dirname stdio.h          # Output: .
    dirname /usr/            # Output: /
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the dirname command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print(get_theme().error_text("dirname: missing operand"))
            return 1

        try:
            for path in args:
                # Remove trailing slashes except for root
                while len(path) > 1 and path.endswith("/"):
                    path = path[:-1]

                # Find last slash
                last_slash = path.rfind("/")

                if last_slash == -1:
                    # No slash found, return current directory
                    result = "."
                elif last_slash == 0:
                    # Slash at beginning, return root
                    result = "/"
                else:
                    # Return everything before last slash
                    result = path[:last_slash]
                    # Remove trailing slashes from result
                    while len(result) > 1 and result.endswith("/"):
                        result = result[:-1]

                self.console.print(result)

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"dirname: {e}"))
            return 1
