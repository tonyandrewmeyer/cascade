"""Lowered command for Cascade.

This module provides implementation for the lowered command that converts
text to lowercase.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LoweredCommand(Command):
    """Convert text to lowercase."""

    name = "lowered"
    help = "Convert text to lowercase"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Convert text to lowercase.

Usage: lowered [OPTIONS] [STRING...]
       echo "TEXT" | lowered

Options:
    -h, --help      Show this help message

If no STRING is provided, reads from stdin.

Examples:
    lowered "HELLO"         # Output: hello
    lowered HELLO WORLD     # Output: hello and world
    echo "HELLO" | lowered  # Output: hello
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the lowered command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if positional_args:
            for text in positional_args:
                self.console.print(text.lower())
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                for line in sys.stdin:
                    self.console.print(line.lower(), end="")
            else:
                self.console.print("[yellow]lowered: no input provided[/yellow]")
                return 1

        return 0
