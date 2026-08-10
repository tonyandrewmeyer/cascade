"""Markdownquote command for Cascade.

This module provides implementation for the markdownquote command that
adds Markdown quote prefix to each line.
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


class MarkdownquoteCommand(Command):
    """Add Markdown quote prefix to each line."""

    name = "markdownquote"
    help = "Add Markdown quote prefix (>) to each line"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Add Markdown quote prefix (>) to each line.

Usage: markdownquote [OPTIONS] [TEXT...]
       echo "text" | markdownquote

Options:
    -h, --help      Show this help message
    -l, --level N   Quote level (default: 1, for nested quotes)

Prefixes each line with "> " for Markdown block quotes.

If no TEXT is provided, reads from stdin.

Examples:
    markdownquote "Hello world"
    # Output: > Hello world

    echo -e "Line 1\\nLine 2" | markdownquote
    # Output:
    # > Line 1
    # > Line 2

    markdownquote -l 2 "Nested quote"
    # Output: >> Nested quote
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the markdownquote command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "l": int,
                "level": int,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        level = flags["l"] or flags["level"] or 1
        prefix = ">" * level + " "

        if positional_args:
            text = ' '.join(positional_args)
            for line in text.split('\n'):
                self.console.print(f"{prefix}{line}")
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                for line in sys.stdin:
                    # Remove trailing newline, add prefix, print with newline
                    self.console.print(f"{prefix}{line.rstrip()}")
            else:
                self.console.print("[yellow]markdownquote: no input provided[/yellow]")
                return 1

        return 0
