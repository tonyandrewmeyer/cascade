"""Implementation of GunzipCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command
from .gzip import GzipCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class GunzipCommand(Command):
    """Implementation of gunzip command."""

    name = "gunzip"
    help = "Decompress gzip files"
    category = "Compression"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute gunzip command."""
        gzip_cmd = GzipCommand(self.shell)
        return gzip_cmd.execute(client, ["-d", *args])
