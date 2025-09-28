"""Implementation of UncompressCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command
from .compress import CompressCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UncompressCommand(Command):
    """Implementation of uncompress command."""

    name = "uncompress"
    help = "Decompress files compressed with compress"
    category = "Compression"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute uncompress command."""
        compress_cmd = CompressCommand(self.shell)
        return compress_cmd.execute(client, ["-d", *args])
