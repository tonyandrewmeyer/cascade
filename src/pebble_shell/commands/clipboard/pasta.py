"""Pasta (paste) command for Cascade.

This module provides implementation for the pasta command that outputs
the local clipboard contents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.clipboard import (
    ClipboardAccessError,
    ClipboardUnavailableError,
    paste_from_clipboard,
)
from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PastaCommand(Command):
    """Output the local clipboard contents."""

    name = "pasta"
    help = "Output the local clipboard contents (paste)"
    category = "Clipboard"

    def show_help(self):
        """Show command help."""
        help_text = """Output the local clipboard contents.

Usage: pasta [OPTIONS]

Options:
    -h, --help      Show this help message
    -n, --no-newline  Don't add trailing newline to output

Outputs the contents of your local system clipboard to stdout.
This can be piped to other commands or used to inspect clipboard contents.

Examples:
    pasta                    # Print clipboard contents
    pasta | grep pattern     # Search clipboard contents
    pasta -n                 # Output without trailing newline
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the pasta command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "n": bool,
                "no-newline": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        no_newline = flags["n"] or flags["no-newline"]

        try:
            text = paste_from_clipboard()
            if no_newline:
                self.console.print(text, end="")
            else:
                # Print with newline if text doesn't already end with one
                if text and not text.endswith("\n"):
                    self.console.print(text)
                else:
                    self.console.print(text, end="")
            return 0
        except ClipboardUnavailableError as e:
            self.console.print(f"[red]pasta: {e}[/red]")
            return 1
        except ClipboardAccessError as e:
            self.console.print(f"[red]pasta: {e}[/red]")
            return 1
