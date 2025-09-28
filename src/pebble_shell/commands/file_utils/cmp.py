"""Implementation of CmpCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
    safe_read_file,
)
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CmpCommand(Command):
    """Implementation of cmp command."""

    name = "cmp"
    help = "Compare two files byte by byte"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Compare two files byte by byte.

Usage: cmp [OPTIONS] FILE1 FILE2

Description:
    Compare two files byte by byte. Exit status is 0 if files are identical,
    1 if different, 2 if trouble.

Options:
    -l, --verbose   Output byte numbers and differing byte values
    -s, --silent    Output nothing; only exit status indicates result
    -h, --help      Show this help message

Examples:
    cmp file1.txt file2.txt
    cmp -l file1.txt file2.txt
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the cmp command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "l": bool,  # verbose
                "s": bool,  # silent
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        verbose = flags.get("l", False)
        silent = flags.get("s", False)

        if len(positional_args) != 2:
            if not silent:
                self.console.print(
                    get_theme().error_text("cmp: missing operand after file1")
                )
                self.console.print("Usage: cmp [OPTIONS] FILE1 FILE2")
            return 2

        file1, file2 = positional_args

        try:
            # Read both files
            data1 = safe_read_file(client, file1, self.shell)
            if data1 is None:
                self.console.print(
                    get_theme().error_text(f"cmp: {file1}: No such file or directory")
                )
                return 2

            data2 = safe_read_file(client, file2, self.shell)
            if data2 is None:
                self.console.print(
                    get_theme().error_text(f"cmp: {file2}: No such file or directory")
                )
                return 2

            if data1 == data2:
                return 0  # Files are identical

            # Files differ
            if silent:
                return 1

            if verbose:
                # Show detailed differences
                min_len = min(len(data1), len(data2))
                for i in range(min_len):
                    if data1[i] != data2[i]:
                        self.console.print(f"{i + 1:8} {data1[i]:3o} {data2[i]:3o}")

                # If files have different lengths
                if len(data1) != len(data2):
                    shorter = file1 if len(data1) < len(data2) else file2
                    self.console.print(f"cmp: EOF on {shorter}")
            else:
                # Find first difference
                min_len = min(len(data1), len(data2))
                for i in range(min_len):
                    if data1[i] != data2[i]:
                        line_num = data1[:i].count("\n") + 1
                        self.console.print(
                            f"{file1} {file2} differ: byte {i + 1}, line {line_num}"
                        )
                        return 1

                # Files differ in length
                if len(data1) != len(data2):
                    shorter = file1 if len(data1) < len(data2) else file2
                    self.console.print(f"cmp: EOF on {shorter}")

            return 1

        except ops.pebble.PathError as e:
            if not silent:
                self.console.print(get_theme().error_text(f"cmp: {e}"))
            return 2
        except Exception as e:
            if not silent:
                self.console.print(get_theme().error_text(f"cmp: {e}"))
            return 2
