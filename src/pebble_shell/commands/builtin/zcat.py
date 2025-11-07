"""Implementation of ZcatCommand."""

from __future__ import annotations

import gzip
import io
from typing import TYPE_CHECKING, Union

import ops

from ...utils import resolve_path
from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class ZcatCommand(Command):
    """Decompress and print .gz files."""

    name = "zcat"
    help = "Decompress and print .gz files. Usage: zcat file [file2...]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute zcat command."""
        if handle_help_flag(self, args):
            return 0
        if validate_min_args(self.shell, args, 1, "zcat file [file2...]"):
            return 1
        for filename in args:
            path = resolve_path(
                self.shell.current_directory, filename, self.shell.home_dir
            )
            try:
                with client.pull(path, encoding=None) as f:
                    compressed_data = f.read()
                    assert isinstance(compressed_data, bytes)
                    with io.BytesIO(compressed_data) as bio:
                        with gzip.open(bio, "rt", errors="replace") as gz:
                            for line in gz:
                                self.console.print(line, end="")
            except (ops.pebble.PathError, gzip.BadGzipFile, OSError) as e:
                self.console.print(f"zcat: {filename}: {e}")
                return 1
        return 0
