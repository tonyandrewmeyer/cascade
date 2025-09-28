"""Implementation of CksumCommand."""

from __future__ import annotations

import binascii
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CksumCommand(Command):
    """Implementation of cksum command."""

    name = "cksum"
    help = "Calculate CRC checksum and byte count"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Calculate CRC checksum and byte count for files.

Usage: cksum [FILE...]

Description:
    Calculate and display the CRC checksum and byte count for each file.
    If no files are specified, read from standard input.

Options:
    -h, --help      Show this help message

Examples:
    cksum file.txt
    cksum file1.txt file2.txt
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the cksum command."""
        if handle_help_flag(self, args):
            return 0

        files = args if args else ["-"]  # stdin if no files
        exit_code = 0

        for file_path in files:
            if file_path == "-":
                # TODO: Handle stdin input
                self.console.print(
                    "[yellow]" + "cksum: reading from stdin not supported" + "[/yellow]"
                )
                continue

            # Read file from remote system
            data = safe_read_file(client, file_path, self.shell)
            if data is None:
                self.console.print(
                    "[red]"
                    + f"cksum: {file_path}: No such file or directory"
                    + "[/red]"
                )
                exit_code = 1
                continue

            try:
                # Calculate CRC32 checksum
                crc = binascii.crc32(data) & 0xFFFFFFFF
                size = len(data)

                self.console.print(f"{crc} {size} {file_path}")

            except Exception as e:
                self.console.print("[red]" + f"cksum: {file_path}: {e}" + "[/red]")
                exit_code = 1

        return exit_code
