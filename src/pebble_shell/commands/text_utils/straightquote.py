"""Straightquote command for Cascade.

This module provides implementation for the straightquote command that
converts smart quotes to straight quotes.
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

# Smart quote mappings
QUOTE_REPLACEMENTS = {
    # Double quotes
    '\u201c': '"',  # Left double quotation mark
    '\u201d': '"',  # Right double quotation mark
    '\u201e': '"',  # Double low-9 quotation mark
    '\u201f': '"',  # Double high-reversed-9 quotation mark
    '\u00ab': '"',  # Left-pointing double angle quotation mark
    '\u00bb': '"',  # Right-pointing double angle quotation mark
    # Single quotes
    '\u2018': "'",  # Left single quotation mark
    '\u2019': "'",  # Right single quotation mark
    '\u201a': "'",  # Single low-9 quotation mark
    '\u201b': "'",  # Single high-reversed-9 quotation mark
    '\u2039': "'",  # Single left-pointing angle quotation mark
    '\u203a': "'",  # Single right-pointing angle quotation mark
    # Prime marks (sometimes used as quotes)
    '\u2032': "'",  # Prime
    '\u2033': '"',  # Double prime
    # Apostrophe variants
    '\u02bc': "'",  # Modifier letter apostrophe
    '\u02bb': "'",  # Modifier letter turned comma
}


class StraightquoteCommand(Command):
    """Convert smart quotes to straight quotes."""

    name = "straightquote"
    help = "Convert smart quotes to straight quotes"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Convert smart quotes to straight quotes.

Usage: straightquote [OPTIONS] [TEXT...]
       echo "text" | straightquote

Options:
    -h, --help      Show this help message

Converts various types of smart/curly quotes to straight ASCII quotes:
    - Left/right double quotes (" ") → "
    - Left/right single quotes (' ') → '
    - Guillemets (« ») → "
    - Prime marks (′ ″) → ' "

If no TEXT is provided, reads from stdin.

Examples:
    straightquote "Hello "World""
    echo ""Smart quotes"" | straightquote
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the straightquote command."""
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
            text = ' '.join(positional_args)
            self.console.print(self._convert_quotes(text))
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                for line in sys.stdin:
                    self.console.print(self._convert_quotes(line), end="")
            else:
                self.console.print("[yellow]straightquote: no input provided[/yellow]")
                return 1

        return 0

    def _convert_quotes(self, text: str) -> str:
        """Convert smart quotes to straight quotes."""
        for smart, straight in QUOTE_REPLACEMENTS.items():
            text = text.replace(smart, straight)
        return text
