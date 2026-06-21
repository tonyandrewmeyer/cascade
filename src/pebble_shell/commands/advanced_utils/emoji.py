"""Emoji lookup command for Cascade.

This module provides implementation for the emoji command that searches
for emojis by name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from ...utils.emoji_lookup import (
    INSTALL_INSTRUCTIONS,
    EmojiUnavailableError,
    is_emoji_available,
    search_emoji,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class EmojiCommand(Command):
    """Search for emojis by name."""

    name = "emoji"
    help = "Search for emojis by name"
    category = "Reference"

    def show_help(self):
        """Show command help."""
        help_text = """Search for emojis by name.

Usage: emoji [OPTIONS] QUERY

Options:
    -h, --help      Show this help message
    -l, --limit N   Maximum results to show (default: 20)
    -c, --copy      Copy first result to clipboard (requires clipboard extra)

Arguments:
    QUERY           Search term to match against emoji names

Requires: pip install pebble-cascade[emoji]

Examples:
    emoji heart         # Find heart-related emojis
    emoji fire          # Find fire emoji
    emoji "thumbs up"   # Search with spaces
    emoji -l 5 cat      # Limit to 5 results
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the emoji command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "l": int,
                "limit": int,
                "c": bool,
                "copy": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        # Check if emoji library is available
        if not is_emoji_available():
            self.console.print(
                f"[red]emoji: emoji library not available[/red]\n{INSTALL_INSTRUCTIONS}"
            )
            return 1

        if not positional_args:
            self.console.print("[red]emoji: missing search query[/red]")
            self.console.print("Usage: emoji <query>")
            return 1

        query = " ".join(positional_args)
        limit = flags["l"] or flags["limit"] or 20
        want_copy = flags["c"] or flags["copy"]

        try:
            results = search_emoji(query, limit=limit)
        except EmojiUnavailableError as e:
            self.console.print(f"[red]{e}[/red]")
            return 1

        if not results:
            self.console.print(f"[yellow]No emojis found matching '{query}'[/yellow]")
            return 1

        # Display results
        for emoji_char, name in results:
            self.console.print(f"{emoji_char}  {name}")

        # Copy first result if requested
        if want_copy and results:
            try:
                from ...utils.clipboard import copy_to_clipboard

                first_emoji = results[0][0]
                copy_to_clipboard(first_emoji)
                self.console.print(
                    f"\n[dim]Copied {first_emoji} to clipboard[/dim]"
                )
            except ImportError:
                self.console.print(
                    "\n[yellow]Clipboard not available. "
                    "Install with: pip install pebble-cascade[clipboard][/yellow]"
                )
            except Exception as e:
                self.console.print(f"\n[yellow]Could not copy to clipboard: {e}[/yellow]")

        return 0
