"""Cpwd command for Cascade.

This module provides implementation for the cpwd command that copies
the current working directory to the local clipboard.
"""

from __future__ import annotations

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


class CpwdCommand(Command):
    """Copy the current working directory to the clipboard."""

    name = "cpwd"
    help = "Copy the current working directory to the clipboard"
    category = "Clipboard"

    def show_help(self):
        """Show command help."""
        help_text = """Copy the current working directory to the clipboard.

Usage: cpwd [OPTIONS]

Options:
    -h, --help      Show this help message
    -q, --quiet     Don't print confirmation message

Copies the current working directory path to your local system clipboard.
This is equivalent to: pwd | copy

Examples:
    cpwd            # Copy current directory to clipboard
    cpwd -q         # Copy quietly without confirmation
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the cpwd command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "q": bool,
                "quiet": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        quiet = flags["q"] or flags["quiet"]

        # Get current working directory from shell state
        cwd = self.shell.cwd

        try:
            copy_to_clipboard(cwd)
            if not quiet:
                self.console.print(f"[green]Copied:[/green] {cwd}")
            return 0
        except ClipboardUnavailableError as e:
            self.console.print(f"[red]cpwd: {e}[/red]")
            return 1
        except ClipboardAccessError as e:
            self.console.print(f"[red]cpwd: {e}[/red]")
            return 1
