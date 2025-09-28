"""Implementation of CommCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file_lines
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CommCommand(Command):
    """Implementation of comm command."""

    name = "comm"
    help = "Compare two sorted files line by line"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Compare two sorted files line by line.

Usage: comm [OPTIONS] FILE1 FILE2

Description:
    Compare two sorted files line by line. Output consists of three columns:
    Column 1: Lines only in FILE1
    Column 2: Lines only in FILE2
    Column 3: Lines in both files

Options:
    -1              Suppress column 1 (lines only in FILE1)
    -2              Suppress column 2 (lines only in FILE2)
    -3              Suppress column 3 (lines in both files)
    -h, --help      Show this help message

Examples:
    comm file1.txt file2.txt
    comm -12 file1.txt file2.txt    # Show only common lines
    comm -3 file1.txt file2.txt     # Show only unique lines
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the comm command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "1": bool,  # suppress column 1
                "2": bool,  # suppress column 2
                "3": bool,  # suppress column 3
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        suppress_1 = flags.get("1", False)
        suppress_2 = flags.get("2", False)
        suppress_3 = flags.get("3", False)

        if len(positional_args) != 2:
            self.console.print(get_theme().error_text("comm: missing operand"))
            self.console.print("Usage: comm [OPTIONS] FILE1 FILE2")
            return 1

        file1, file2 = positional_args

        try:
            # Read both files
            lines1 = safe_read_file_lines(client, file1, self.shell)
            if lines1 is None:
                return 1

            lines2 = safe_read_file_lines(client, file2, self.shell)
            if lines2 is None:
                return 1

            # Compare sorted lines
            i1 = i2 = 0

            while i1 < len(lines1) and i2 < len(lines2):
                line1 = lines1[i1]
                line2 = lines2[i2]

                if line1 < line2:
                    # Line only in file1
                    if not suppress_1:
                        prefix = ""
                        if not suppress_2:
                            prefix += "\t"
                        if not suppress_3:
                            prefix += "\t"
                        self.console.print(f"{line1}")
                    i1 += 1
                elif line1 > line2:
                    # Line only in file2
                    if not suppress_2:
                        prefix = ""
                        if not suppress_1:
                            prefix += "\t"
                        if not suppress_3:
                            prefix += "\t"
                        self.console.print(f"{prefix}{line2}")
                    i2 += 1
                else:
                    # Line in both files
                    if not suppress_3:
                        prefix = ""
                        if not suppress_1:
                            prefix += "\t"
                        if not suppress_2:
                            prefix += "\t"
                        self.console.print(f"{prefix}{line1}")
                    i1 += 1
                    i2 += 1

            # Output remaining lines from file1
            while i1 < len(lines1):
                if not suppress_1:
                    self.console.print(lines1[i1])
                i1 += 1

            # Output remaining lines from file2
            while i2 < len(lines2):
                if not suppress_2:
                    prefix = ""
                    if not suppress_1:
                        prefix += "\t"
                    if not suppress_3:
                        prefix += "\t"
                    self.console.print(f"{prefix}{lines2[i2]}")
                i2 += 1

            return 0

        except ops.pebble.PathError as e:
            self.console.print(get_theme().error_text(f"comm: {e}"))
            return 1
        except Exception as e:
            self.console.print(get_theme().error_text(f"comm: {e}"))
            return 1
