"""Implementation of DateCommand."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    get_boot_time_from_stat,
    parse_proc_uptime,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DateCommand(Command):
    """Show the current date and time."""

    name = "date"
    help = "Show the current date and time. Usage: date [+FORMAT]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the date command."""
        if handle_help_flag(self, args):
            return 0

        try:
            uptime_info = parse_proc_uptime(client)
            boot_time = get_boot_time_from_stat(client)
            current_time = boot_time + int(uptime_info["uptime_seconds"])

            dt = datetime.datetime.fromtimestamp(current_time)

            if args and args[0].startswith("+"):
                fmt = args[0][1:]
                try:
                    self.console.print(dt.strftime(fmt))
                except Exception as e:
                    self.console.print(f"date: invalid format: {fmt} ({e})")
                    return 1
            else:
                self.console.print(dt.strftime("%a %b %d %H:%M:%S %Z %Y"))

            return 0
        except ProcReadError as e:
            self.console.print(f"date: error reading system time: {e}")
            return 1
