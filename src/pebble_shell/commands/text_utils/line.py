"""Line command for Cascade.

This module provides implementation for the line command that extracts
a specific line number from input.
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


class LineCommand(Command):
    """Extract a specific line number from input."""

    name = "line"
    help = "Extract a specific line number from input"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Extract a specific line number from input.

Usage: line [OPTIONS] LINE_NUMBER
       cat file | line 10

Options:
    -h, --help      Show this help message

Arguments:
    LINE_NUMBER     The line number to extract (1-indexed)

Negative line numbers count from the end (-1 is the last line).

Examples:
    cat file.txt | line 1     # Get first line
    cat file.txt | line 10    # Get line 10
    cat file.txt | line -1    # Get last line
    cat file.txt | line -2    # Get second to last line
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the line command."""
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

        if not positional_args:
            self.console.print("[red]line: missing line number argument[/red]")
            return 1

        try:
            line_num = int(positional_args[0])
        except ValueError:
            self.console.print(f"[red]line: invalid line number: {positional_args[0]}[/red]")
            return 1

        if line_num == 0:
            self.console.print("[red]line: line numbers are 1-indexed (use 1 for first line)[/red]")
            return 1

        # Read from stdin
        if not sys.stdin.isatty():
            lines = sys.stdin.readlines()
        else:
            self.console.print("[yellow]line: no input provided (pipe data to this command)[/yellow]")
            return 1

        if not lines:
            self.console.print("[yellow]line: input is empty[/yellow]")
            return 1

        # Handle negative indices (Python-style, but 1-indexed)
        if line_num < 0:
            idx = line_num  # -1 means last, -2 means second to last, etc.
        else:
            idx = line_num - 1  # Convert to 0-indexed

        try:
            selected_line = lines[idx]
            self.console.print(selected_line, end="")
            return 0
        except IndexError:
            total_lines = len(lines)
            self.console.print(f"[red]line: line {line_num} out of range (file has {total_lines} lines)[/red]")
            return 1
