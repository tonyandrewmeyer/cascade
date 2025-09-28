"""Implementation of BasenameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in one of the file categories.
class BasenameCommand(Command):
    """Strip directory and suffix from filenames."""

    name = "basename"
    help = "Strip directory and suffix from filenames"
    category = "File"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the basename command."""
        return self._execute_basename(client, args)

    def _execute_basename(self, client: ClientType, args: list[str]) -> int:
        if not args:
            self.console.print("Usage: basename NAME [SUFFIX]")
            return 1

        path = args[0]
        suffix = args[1] if len(args) > 1 else None

        # Get basename
        base = path.rstrip("/").split("/")[-1] if "/" in path else path

        # Remove suffix if provided
        if suffix and base.endswith(suffix):
            base = base[: -len(suffix)]

        self.console.print(base)
        return 0
