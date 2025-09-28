"""Pause for a given number of seconds."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class SleepCommand(Command):
    """Pause for a given number of seconds."""

    name = "sleep"
    help = "Pause for a given number of seconds. Usage: sleep SECONDS"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute sleep command."""
        if handle_help_flag(self, args):
            return 0
        if not validate_min_args(self.shell, args, 1, "sleep SECONDS"):
            return 1
        try:
            seconds = float(args[0])
        except ValueError:
            self.console.print(f"sleep: invalid time interval '{args[0]}'")
            return 1
        if seconds < 0:
            self.console.print("sleep: time may not be negative")
            return 1
        time.sleep(seconds)
        return 0
