"""Alphabet command for Cascade.

This module provides implementation for the alphabet command that prints
the English alphabet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class AlphabetCommand(Command):
    """Print the English alphabet."""

    name = "alphabet"
    help = "Print the English alphabet"
    category = "Reference"

    def show_help(self):
        """Show command help."""
        help_text = """Print the English alphabet.

Usage: alphabet [OPTIONS]

Options:
    -h, --help      Show this help message
    -u, --upper     Print uppercase only
    -l, --lower     Print lowercase only
    -n, --newline   Print each letter on a new line

Examples:
    alphabet        # Print both upper and lowercase
    alphabet -u     # Print uppercase only
    alphabet -l     # Print lowercase only
    alphabet -n     # Each letter on its own line
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the alphabet command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "u": bool,
                "upper": bool,
                "l": bool,
                "lower": bool,
                "n": bool,
                "newline": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        upper_only = flags["u"] or flags["upper"]
        lower_only = flags["l"] or flags["lower"]
        use_newlines = flags["n"] or flags["newline"]

        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lowercase = "abcdefghijklmnopqrstuvwxyz"

        if use_newlines:
            if upper_only:
                for char in uppercase:
                    self.console.print(char)
            elif lower_only:
                for char in lowercase:
                    self.console.print(char)
            else:
                for u, l in zip(uppercase, lowercase):
                    self.console.print(f"{u} {l}")
        else:
            if upper_only:
                self.console.print(uppercase)
            elif lower_only:
                self.console.print(lowercase)
            else:
                self.console.print(uppercase)
                self.console.print(lowercase)

        return 0
