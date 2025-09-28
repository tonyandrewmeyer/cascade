"""Implementation of TimeCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TimeCommand(Command):
    """Command for timing the execution of other commands."""
    name = "time"
    help = "Time the execution of a command. Usage: time COMMAND [ARGS...]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the time command to measure command execution time."""
        if handle_help_flag(self, args):
            return 0
        if not args:
            self.console.print("time: missing command")
            return 1
        start = time.perf_counter()
        try:
            process = client.exec(args)
            process.wait_output()
            rc = 0
        except ops.pebble.ExecError[str] as e:
            if e.stdout:
                self.console.print(e.stdout, end="")
            if e.stderr:
                self.console.print(e.stderr, end="")
            rc = e.exit_code
        end = time.perf_counter()
        elapsed = end - start
        mins = int(elapsed // 60)
        secs = elapsed % 60
        self.console.print(f"real{mins}m{secs:06.3f}s")
        # user/sys times not available without resource module and local exec
        return rc
