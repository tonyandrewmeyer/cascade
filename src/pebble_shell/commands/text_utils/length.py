"""Length command for Cascade.

This module provides implementation for the length command that returns
the character count of a string.
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


class LengthCommand(Command):
    """Return the character count of a string."""

    name = "length"
    help = "Return the character count of a string"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Return the character count of a string.

Usage: length [OPTIONS] [STRING...]
       echo "text" | length

Options:
    -h, --help      Show this help message
    -b, --bytes     Count bytes instead of characters
    -w, --words     Count words instead of characters
    -l, --lines     Count lines instead of characters

If no STRING is provided, reads from stdin.

Examples:
    length "hello"          # Output: 5
    length hello world      # Output: 5 and 5
    echo "hello" | length   # Output: 5
    length -w "hello world" # Output: 2
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the length command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "b": bool,
                "bytes": bool,
                "w": bool,
                "words": bool,
                "l": bool,
                "lines": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        count_bytes = flags["b"] or flags["bytes"]
        count_words = flags["w"] or flags["words"]
        count_lines = flags["l"] or flags["lines"]

        if positional_args:
            for text in positional_args:
                count = self._count(text, count_bytes, count_words, count_lines)
                self.console.print(str(count))
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                text = sys.stdin.read()
                # Remove trailing newline for character count to match echo behavior
                if not count_lines and text.endswith('\n'):
                    text = text[:-1]
                count = self._count(text, count_bytes, count_words, count_lines)
                self.console.print(str(count))
            else:
                self.console.print("[yellow]length: no input provided[/yellow]")
                return 1

        return 0

    def _count(self, text: str, count_bytes: bool, count_words: bool, count_lines: bool) -> int:
        """Count characters, bytes, words, or lines in text."""
        if count_bytes:
            return len(text.encode('utf-8'))
        elif count_words:
            return len(text.split())
        elif count_lines:
            return text.count('\n') + (1 if text and not text.endswith('\n') else 0)
        else:
            return len(text)
