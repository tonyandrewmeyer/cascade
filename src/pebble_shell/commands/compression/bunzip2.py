"""Implementation of BunzipCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command
from .bzip2 import BzipCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class BunzipCommand(Command):
    """Implementation of bunzip2 command."""

    name = "bunzip2"
    help = "Decompress bzip2 files"
    category = "Compression"

    def execute(
        self,
        client: ClientType,
        args: list[str],
    ) -> int:
        """Execute the bunzip2 command."""
        # Delegate to bzip2 with -d flag
        bzip_cmd = BzipCommand(self.shell)
        return bzip_cmd.execute(client, ["-d", *args])
