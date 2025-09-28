"""Implementation of SumCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class SumCommand(Command):
    """Implementation of sum command."""

    name = "sum"
    help = "Calculate and display checksums"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Calculate and display checksums.

Usage: sum [OPTIONS] [FILE...]

Description:
    Calculate and display BSD-style or System V-style checksums.
    If no files are specified, read from standard input.

Options:
    -r              Use BSD sum algorithm (default)
    -s, --sysv      Use System V sum algorithm
    -h, --help      Show this help message

Examples:
    sum file.txt
    sum -s file1.txt file2.txt
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the sum command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "r": bool,  # BSD algorithm (default)
                "s": bool,  # System V algorithm
                "sysv": bool,  # System V algorithm
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        use_sysv = flags.get("s", False) or flags.get("sysv", False)
        files = positional_args if positional_args else ["-"]
        exit_code = 0

        for file_path in files:
            try:
                if file_path == "-":
                    # TODO: Handle stdin input
                    self.console.print(
                        get_theme().warning_text(
                            "sum: reading from stdin not supported"
                        )
                    )
                    continue

                # Read file from remote system
                data = safe_read_file(client, file_path, self.shell)
                if data is None:
                    self.console.print(
                        get_theme().error_text(
                            f"sum: {file_path}: No such file or directory"
                        )
                    )
                    exit_code = 1
                    continue

                # Convert string to bytes for checksum calculation
                data_bytes = data.encode("utf-8")

                if use_sysv:
                    # System V algorithm: sum of all bytes
                    checksum = sum(data_bytes) & 0xFFFF
                    blocks = (len(data_bytes) + 511) // 512  # 512-byte blocks
                    self.console.print(f"{checksum} {blocks} {file_path}")
                else:
                    # BSD algorithm: rotating checksum
                    checksum = 0
                    for byte in data_bytes:
                        checksum = ((checksum >> 1) | ((checksum & 1) << 15)) + byte
                        checksum &= 0xFFFF

                    blocks = (len(data_bytes) + 1023) // 1024  # 1024-byte blocks
                    self.console.print(f"{checksum:05d} {blocks:5d} {file_path}")

            except Exception as e:
                self.console.print(get_theme().error_text(f"sum: {file_path}: {e}"))
                exit_code = 1

        return exit_code
