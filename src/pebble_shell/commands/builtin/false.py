"""Exit with failure (exit code 1)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class FalseCommand(Command):
    """Exit with failure (exit code 1)."""

    name = "false"
    help = "Exit with failure (exit code 1)"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the false command."""
        if handle_help_flag(self, args):
            return 0
        return 1
