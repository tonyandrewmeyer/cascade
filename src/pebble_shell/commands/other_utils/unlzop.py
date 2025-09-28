"""Implementation of UnlzopCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the compression category.
class UnlzopCommand(Command):
    """Decompress lzop files."""

    name = "unlzop"
    help = "Decompress lzop files"
    category = "Compression"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the unlzop command."""
        return self._execute_unlzop(client, args)

    def _execute_unlzop(self, client: ClientType, args: list[str]) -> int:
        # TODO: Implement this!
        return 1
