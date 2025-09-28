"""Implementation of TtysizeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TtysizeCommand(Command):
    """Implementation of ttysize command."""

    name = "ttysize"
    help = "Display terminal size"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """Display terminal size.

Usage: ttysize

Description:
    Print the terminal size as columns and rows.

Examples:
    ttysize         # Display terminal size
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the ttysize command."""
        if handle_help_flag(self, args):
            return 0

        try:
            import os
            import shutil

            # Try to get terminal size
            try:
                # First try shutil.get_terminal_size()
                size = shutil.get_terminal_size()
                columns = size.columns
                rows = size.lines
            except Exception:
                # Fallback to environment variables
                columns = int(os.environ.get("COLUMNS", 80))
                rows = int(os.environ.get("LINES", 24))

            self.console.print(f"{columns} {rows}")
            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"ttysize: {e}"))
            return 1
