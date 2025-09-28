"""Simple remote command execution (alias for exec)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command
from .exec import ExecCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class RunCommand(Command):
    """Simple remote command execution (alias for exec)."""

    name = "run"
    help = "Run a command on the remote system"
    category = "Remote Execution"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute run command."""
        if handle_help_flag(self, args):
            return 0
        if not args:
            self.console.print("Usage: run <command> [args...]")
            self.console.print("Example: run ps aux")
            return 1

        try:
            exec_cmd = ExecCommand(self.shell)
            return exec_cmd.execute(client, args)
        except (ops.pebble.ExecError, ops.pebble.APIError, TypeError) as e:
            self.console.print(f"run: error executing command: {e}")
            return 1
