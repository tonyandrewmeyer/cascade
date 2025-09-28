"""Implementation of BzcatCommand."""

from __future__ import annotations

import bz2
import io
import os
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: This should be in the compression group.
class BzcatCommand(Command):
    """Decompress and print .bz2 files."""

    name = "bzcat"
    help = "Decompress and print .bz2 files. Usage: bzcat file [file2...]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute bzcat command."""
        if handle_help_flag(self, args):
            return 0
        cwd = self.shell.current_directory
        if validate_min_args(self.shell, args, 1, "bzcat file [file2...]"):
            return 1
        for filename in args:
            path = filename if os.path.isabs(filename) else os.path.join(cwd, filename)
            try:
                with client.pull(path, encoding=None) as f:
                    compressed_data = f.read()
            except ops.pebble.PathError as e:
                self.console.print(f"bzcat: {e}")
                return 1
            assert isinstance(compressed_data, bytes)
            with io.BytesIO(compressed_data) as bio:
                with bz2.open(bio, "rt", errors="replace") as f:
                    for line in f:
                        self.console.print(line, end="")
        return 0
