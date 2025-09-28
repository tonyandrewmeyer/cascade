"""Print current working directory."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PwdCommand(Command):
    """Print current working directory."""

    name = "pwd"
    help = "Print current directory"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute pwd command."""
        if handle_help_flag(self, args):
            return 0

        if not self.validate_args(args, min_args=0, max_args=0):
            return 1

        self.console.print(self.shell.current_directory)
        return 0
