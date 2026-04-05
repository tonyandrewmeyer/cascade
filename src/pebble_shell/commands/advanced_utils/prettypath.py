"""Prettypath command for Cascade.

This module provides implementation for the prettypath command that displays
the PATH environment variable with each entry on a separate line.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PrettypathCommand(Command):
    """Display PATH with each entry on a separate line."""

    name = "prettypath"
    help = "Display PATH with each entry on a separate line"
    category = "System Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Display PATH with each entry on a separate line.

Usage: prettypath [OPTIONS]

Options:
    -h, --help      Show this help message
    -n, --numbered  Show line numbers
    -c, --check     Check if each path exists

Makes the PATH environment variable more readable by displaying
each directory on its own line.

Examples:
    prettypath          # Show PATH entries
    prettypath -n       # Show with line numbers
    prettypath -c       # Show with existence check
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the prettypath command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "n": bool,
                "numbered": bool,
                "c": bool,
                "check": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        numbered = flags["n"] or flags["numbered"]
        check = flags["c"] or flags["check"]

        path = os.environ.get("PATH", "")
        if not path:
            self.console.print("[yellow]prettypath: PATH is not set[/yellow]")
            return 1

        entries = path.split(os.pathsep)

        for i, entry in enumerate(entries, 1):
            if numbered:
                prefix = f"[dim]{i:3}.[/dim] "
            else:
                prefix = ""

            if check:
                # Check if path exists in the container
                try:
                    client.list_files(entry)
                    status = "[green]✓[/green]"
                except Exception:
                    status = "[red]✗[/red]"
                self.console.print(f"{prefix}{entry} {status}")
            else:
                self.console.print(f"{prefix}{entry}")

        return 0
