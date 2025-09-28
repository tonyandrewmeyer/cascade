"""Implementation of LzmacatCommand."""

from __future__ import annotations

import lzma
from typing import TYPE_CHECKING, Union

import ops

from .._base import Command
from pebble_shell.utils.command_helpers import safe_read_file

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the compression category.
class LzmacatCommand(Command):
    """Display LZMA compressed files."""

    name = "lzmacat"
    help = "Display LZMA compressed files"
    category = "Compression"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the lzmacat command."""
        return self._execute_lzmacat(client, args)

    def _execute_lzmacat(self, client: ClientType, args: list[str]) -> int:
        if not args:
            self.console.print("Usage: lzmacat [files...]")
            return 1

        for file_path in args:
            try:
                compressed_content = safe_read_file(client, file_path, self.shell)
                if compressed_content is not None:
                    content = lzma.decompress(compressed_content.encode())
                    self.console.print(content.decode(), end="")
            except Exception as e:  # noqa: PERF203  # needed for robust file processing
                self.console.print(f"lzmacat: {file_path}: {e}")
                return 1

        return 0
