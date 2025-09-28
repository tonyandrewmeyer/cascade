"""Implementation of TimeoutCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TimeoutCommand(Command):
    name = "timeout"
    help = "Run a command with a time limit. Usage: timeout SECONDS COMMAND [ARGS...]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        if handle_help_flag(self, args):
            return 0
        if not args or len(args) < 3:
            self.console.print(
                "Usage: timeout [--preserve-status] SECONDS COMMAND [ARGS...]"
            )
            return 1
        try:
            seconds = float(args[0])
            if seconds <= 0:
                self.console.print("timeout: time must be positive")
                return 1
        except ValueError:
            self.console.print(f"timeout: invalid time interval '{args[0]}'")
            return 1
        cmd = args[1:]
        if args[0] == "--preserve-status":
            preserve_status = True
            cmd = args[2:]
        else:
            preserve_status = False
        process = client.exec(cmd, timeout=seconds)

        try:
            stdout, stderr = process.wait_output()
            if stdout:
                self.console.print(stdout, end="")
            if stderr:
                self.console.print(stderr, end="")
            return 0
        except ops.pebble.TimeoutError:
            return 124
        except ops.pebble.ExecError[str] as e:
            if e.stdout:
                self.console.print(e.stdout, end="")
            if e.stderr:
                self.console.print(e.stderr, end="")
            if preserve_status:
                return e.exit_code
            return 125
