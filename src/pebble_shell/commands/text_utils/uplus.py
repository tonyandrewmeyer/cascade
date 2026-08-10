"""Unicode lookup command for Cascade.

This module provides implementation for the u+ command that looks up
Unicode characters by their code point.
"""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UplusCommand(Command):
    """Look up Unicode characters by code point."""

    name = "u+"
    help = "Look up Unicode characters by code point"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Look up Unicode characters by code point.

Usage: u+ [OPTIONS] CODEPOINT [CODEPOINT...]

Options:
    -h, --help      Show this help message
    -c, --char-only Only output the character (no name)
    -n, --name-only Only output the name (no character)

Arguments:
    CODEPOINT       Hexadecimal Unicode code point (e.g., 2025, 1F600)
                    Can optionally include U+ prefix (e.g., U+2025)

Examples:
    u+ 00f1             # ñ, LATIN SMALL LETTER N WITH TILDE
    u+ 1F600            # 😀, GRINNING FACE
    u+ U+2665           # ♥, BLACK HEART SUIT
    u+ 41 42 43         # Look up multiple code points
    u+ -c 2665          # Just output ♥
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the u+ command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "c": bool,
                "char-only": bool,
                "n": bool,
                "name-only": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if not positional_args:
            self.console.print("[red]u+: missing code point argument[/red]")
            return 1

        char_only = flags["c"] or flags["char-only"]
        name_only = flags["n"] or flags["name-only"]

        exit_code = 0
        for codepoint in positional_args:
            # Remove U+ or u+ prefix if present
            codepoint = codepoint.upper()
            if codepoint.startswith("U+"):
                codepoint = codepoint[2:]

            try:
                # Parse hex code point
                code = int(codepoint, 16)

                # Validate range
                if code < 0 or code > 0x10FFFF:
                    self.console.print(f"[red]u+: code point out of range: {codepoint}[/red]")
                    exit_code = 1
                    continue

                # Get the character
                char = chr(code)

                # Get the name
                try:
                    name = unicodedata.name(char)
                except ValueError:
                    # Some characters don't have names
                    name = "(unnamed)"

                # Output based on flags
                if char_only:
                    self.console.print(char)
                elif name_only:
                    self.console.print(name)
                else:
                    # Full output: character, name
                    # Use repr for control characters that wouldn't display well
                    if unicodedata.category(char).startswith("C") and char not in "\t\n":
                        char_display = f"[dim](control character)[/dim]"
                    else:
                        char_display = char
                    self.console.print(f"{char_display}, {name}")

            except ValueError:
                self.console.print(f"[red]u+: invalid hex code point: {codepoint}[/red]")
                exit_code = 1

        return exit_code
