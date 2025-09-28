"""Implementation of ArCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: This should go to the compression category.
class ArCommand(Command):
    """Create, modify, and extract from archives."""

    name = "ar"
    help = "Create, modify, and extract from archives"
    category = "Archive"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the ar command."""
        return self._execute_ar(client, args)

    def _execute_ar(self, client: ClientType, args: list[str]) -> int:
        if not args:
            self.console.print("Usage: ar [options] archive [files...]")
            return 1

        # TODO: Implement this!
        self.console.print(f"ar command with args: {' '.join(args)}")
        return 0
