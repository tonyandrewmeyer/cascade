"""Implementation of HexdumpCommand."""

from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, BinaryIO, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class HexdumpCommand(Command):
    """Display file contents in hexadecimal (hexdump)."""

    name = "hexdump"
    help = "Display file contents in hexadecimal. Usage: hexdump [-C] [file]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute hexdump command."""
        if handle_help_flag(self, args):
            return 0
        canonical = False
        files: list[str] = []
        for arg in args:
            if arg == "-C":
                canonical = True
            else:
                files.append(arg)
        if not files:
            self.console.print("hexdump: no files specified")
            return 1
        cwd = self.shell.current_directory
        exit_code = 0
        for filename in files:
            path = filename if os.path.isabs(filename) else os.path.join(cwd, filename)
            try:
                with client.pull(path, encoding=None) as f:
                    assert isinstance(f, bytes)
                    self._hexdump(io.BytesIO(f), canonical)
            except (ops.pebble.PathError, ops.pebble.APIError) as e:
                self.console.print(f"hexdump: {filename}: {e}")
                exit_code = 1
        return exit_code

    def _hexdump(self, f: BinaryIO, canonical: bool):
        offset = 0
        while True:
            chunk = f.read(16)
            if not chunk:
                break
            hex_bytes = " ".join(f"{b:02x}" for b in chunk)
            ascii_bytes = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            if canonical:
                # Group hex bytes for -C
                hex_groups = [hex_bytes[i : i + 8] for i in range(0, len(hex_bytes), 8)]
                hex_str = "  ".join(hex_groups)
                self.console.print(f"{offset:08x}  {hex_str:<23}  |{ascii_bytes}|")
            else:
                self.console.print(f"{offset:08x}: {hex_bytes:<47}  {ascii_bytes}")
            offset += len(chunk)
