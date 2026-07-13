"""Uppered command for Cascade.

This module provides implementation for the uppered command that converts
text to uppercase.
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


class UpperedCommand(Command):
    """Convert text to uppercase."""

    name = "uppered"
    help = "Convert text to uppercase"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Convert text to uppercase.

Usage: uppered [OPTIONS] [STRING...]
       echo "text" | uppered

Options:
    -h, --help      Show this help message

If no STRING is provided, reads from stdin.

Examples:
    uppered "hello"         # Output: HELLO
    uppered hello world     # Output: HELLO and WORLD
    echo "hello" | uppered  # Output: HELLO
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the uppered command."""
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
                self.console.print(text.upper())
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                for line in sys.stdin:
                    self.console.print(line.upper(), end="")
            else:
                self.console.print("[yellow]uppered: no input provided[/yellow]")
                return 1

        return 0
