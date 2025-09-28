"""Implementation of UnlzmaCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command
from .lzma import LzmaCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UnlzmaCommand(Command):
    """Implementation of unlzma command."""

    name = "unlzma"
    help = "Decompress LZMA files"
    category = "Compression"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute unlzma command."""
        lzma_cmd = LzmaCommand(self.shell)
        return lzma_cmd.execute(client, ["-d", *args])
