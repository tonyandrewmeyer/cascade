"""Copy command for Cascade.

This module provides implementation for the copy command that copies
text to the local clipboard.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Union

import ops

from ...utils.clipboard import (
    ClipboardAccessError,
    ClipboardUnavailableError,
    copy_to_clipboard,
)
from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CopyCommand(Command):
    """Copy text to the local clipboard."""

    name = "copy"
    help = "Copy text to the local clipboard"
    category = "Clipboard"

    def show_help(self):
        """Show command help."""
        help_text = """Copy text to the local clipboard.

Usage: copy [OPTIONS] [TEXT...]
       <command> | copy

Options:
    -h, --help      Show this help message
    -n, --no-newline  Don't add trailing newline when copying from stdin
    -q, --quiet     Don't print confirmation message

Copies text to your local system clipboard. If TEXT is provided, copies
that text. Otherwise, reads from stdin (useful for piping).

Examples:
    copy "Hello, World!"           # Copy text directly
    cat /etc/os-release | copy     # Copy command output
    pwd | copy                     # Copy current directory
    echo "secret" | copy -q        # Copy quietly
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the copy command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "n": bool,
                "no-newline": bool,
                "q": bool,
                "quiet": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        no_newline = flags["n"] or flags["no-newline"]
        quiet = flags["q"] or flags["quiet"]

        # Get text to copy
        if positional_args:
            text = " ".join(positional_args)
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                text = sys.stdin.read()
                # Strip trailing newline if requested
                if no_newline and text.endswith("\n"):
                    text = text[:-1]
            else:
                self.console.print("[yellow]copy: no input provided[/yellow]")
                self.console.print("Usage: copy TEXT or <command> | copy")
                return 1

        try:
            copy_to_clipboard(text)
            if not quiet:
                # Show confirmation with preview
                preview = text[:50] + "..." if len(text) > 50 else text
                # Escape any Rich markup in the preview
                preview = preview.replace("[", "\\[")
                preview = preview.replace("\n", "\\n")
                self.console.print(f"[green]Copied:[/green] {preview}")
            return 0
        except ClipboardUnavailableError as e:
            self.console.print(f"[red]copy: {e}[/red]")
            return 1
        except ClipboardAccessError as e:
            self.console.print(f"[red]copy: {e}[/red]")
            return 1
