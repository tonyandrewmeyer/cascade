"""Seq command for Cascade.

This module provides implementation for the seq command that generates
sequences of numbers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Move this to an exceptions.py module.
class TextUtilsError(Exception):
    """Exception raised for text processing errors."""


class SeqCommand(Command):
    """Implementation of seq command."""

    name = "seq"
    help = "Generate sequences of numbers"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Generate sequences of numbers.

Usage: seq [OPTIONS] LAST
       seq [OPTIONS] FIRST LAST
       seq [OPTIONS] FIRST INCREMENT LAST

Options:
    -h, --help      Show this help message
    -s, --separator SEP  Use SEP instead of newline
    -w, --equal-width    Pad numbers with leading zeros
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the seq command."""
        if handle_help_flag(self, args):
            return 0

        result = parse_flags(
            args,
            {
                "f": str,  # format string
                "s": str,  # separator
                "w": bool,  # equal width (zero padding)
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        format_str = flags.get("f")
        separator = flags.get("s", "\n")
        equal_width = flags.get("w", False)

        # Parse positional arguments
        if len(positional_args) == 1:
            # seq LAST
            first = 1.0
            increment = 1.0
            last = float(positional_args[0])
        elif len(positional_args) == 2:
            # seq FIRST LAST
            first = float(positional_args[0])
            increment = 1.0
            last = float(positional_args[1])
        elif len(positional_args) == 3:
            # seq FIRST INCREMENT LAST
            first = float(positional_args[0])
            increment = float(positional_args[1])
            last = float(positional_args[2])
        else:
            self.console.print(
                get_theme().error_text("seq: invalid number of arguments")
            )
            return 1

        if increment == 0:
            raise TextUtilsError("increment cannot be zero")

        try:
            numbers = self._generate_sequence(first, increment, last)
            if equal_width:
                # Determine the maximum width needed
                max_width = max(len(str(int(num))) for num in numbers)
                formatted_numbers = [
                    f"{int(num):0{max_width}d}" if num.is_integer() else str(num)
                    for num in numbers
                ]
            elif format_str:
                # Use custom format
                formatted_numbers = [format_str % num for num in numbers]
            else:
                # Default format
                formatted_numbers = [
                    str(int(num)) if num.is_integer() else str(num) for num in numbers
                ]

            output = separator.join(formatted_numbers)
            if separator != "\n":
                output += "\n"

            self.console.print(output, end="")
            return 0

        except (ValueError, TextUtilsError) as e:
            self.console.print(get_theme().error_text(f"seq: {e}"))
            return 1

    def _generate_sequence(
        self, first: float, increment: float, last: float
    ) -> list[float]:
        """Generate the sequence of numbers."""
        # Calculate number of steps
        if increment > 0 and first <= last:
            steps = int((last - first) / increment) + 1
        elif increment < 0 and first >= last:
            steps = int((first - last) / abs(increment)) + 1
        else:
            return []

        # Generate sequence using range-like logic
        return [first + i * increment for i in range(steps)]
