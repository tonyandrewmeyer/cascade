"""Hoy command for Cascade.

This module provides implementation for the hoy command that prints
the current date in ISO format (YYYY-MM-DD).
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from ...utils.proc_reader import get_boot_time_from_stat, parse_proc_uptime
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class HoyCommand(Command):
    """Print today's date in ISO format."""

    name = "hoy"
    help = "Print today's date in ISO format (YYYY-MM-DD)"
    category = "System Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Print today's date in ISO format.

Usage: hoy [OPTIONS]

Options:
    -h, --help      Show this help message

Output format: YYYY-MM-DD (e.g., 2024-01-15)

Examples:
    hoy             # Print today's date
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the hoy command."""
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
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        try:
            uptime_info = parse_proc_uptime(client)
            boot_time = get_boot_time_from_stat(client)
            current_time = boot_time + int(uptime_info["uptime_seconds"])

            dt = datetime.datetime.fromtimestamp(current_time)
            self.console.print(dt.strftime("%Y-%m-%d"))
            return 0
        except Exception as e:
            self.console.print(f"[red]hoy: error reading system time: {e}[/red]")
            return 1
