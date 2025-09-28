"""Implementation of YesCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class YesCommand(Command):
    """Implementation of yes command."""

    name = "yes"
    help = "Output a string repeatedly"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Output a string repeatedly.

Usage: yes [STRING]

Description:
    Repeatedly output STRING, or 'y' if no string specified.
    Continues until interrupted.

Options:
    -h, --help      Show this help message

Examples:
    yes             # Output 'y' repeatedly
    yes hello       # Output 'hello' repeatedly
    yes "test data" # Output 'test data' repeatedly
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the yes command."""
        if handle_help_flag(self, args):
            return 0

        # Determine output string
        output_string = " ".join(args) if args else "y"

        try:
            while True:
                self.console.print(output_string)
                time.sleep(0.001)  # Small delay to prevent overwhelming
        except KeyboardInterrupt:
            return 0
