"""Implementation of HdCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .hexdump import HexdumpCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class HdCommand(HexdumpCommand):
    """Implementation of hd command (alias for hexdump -C)."""

    name = "hd"
    help = "Display file contents in hexadecimal (canonical format)"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the hd command."""
        # hd is equivalent to hexdump -C, so prepend -C to args
        return super().execute(client, ["-C", *args])
