"""Unexpand command for Cascade.

This module provides implementation for the unexpand command that converts
spaces to tabs.
"""

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


# TODO: Move this to an exceptions.py module.
class TextUtilsError(Exception):
    """Exception raised for text processing errors."""


class UnexpandCommand(Command):
    """Implementation of unexpand command."""

    name = "unexpand"
    help = "Convert spaces to tabs"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the unexpand command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "t": str,  # tab stops
                "a": bool,  # convert all whitespace
                "first-only": bool,  # only convert initial spaces
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        tab_stops = flags.get("t") or "8"
        convert_all = flags.get("a", False)
        first_only = flags.get("first-only", not convert_all)

        try:
            # Parse tab stops
            if "," in tab_stops:
                stops = [int(x) for x in tab_stops.split(",")]
            else:
                tab_size = int(tab_stops)
                stops = None

            if not positional_args:
                self.console.print(
                    get_theme().warning_text(
                        "unexpand: reading from stdin not supported"
                    )
                )
                return 1

            for file_path in positional_args:
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    return 1

                if stops:
                    unexpanded = self._unexpand_with_stops(content, stops, first_only)
                else:
                    unexpanded = self._unexpand_with_size(content, tab_size, first_only)

                self.console.print(unexpanded, end="")

            return 0

        except (ValueError, TextUtilsError) as e:
            self.console.print(get_theme().error_text(f"unexpand: {e}"))
            return 1

    def _unexpand_with_size(self, content: str, tab_size: int, first_only: bool) -> str:
        """Convert spaces to tabs using a fixed tab size."""
        lines = content.splitlines(keepends=True)
        result = []

        for line in lines:
            if first_only:
                # Only convert leading spaces
                leading_spaces = 0
                for char in line:
                    if char == " ":
                        leading_spaces += 1
                    else:
                        break

                if leading_spaces >= tab_size:
                    tabs = leading_spaces // tab_size
                    remaining_spaces = leading_spaces % tab_size
                    unexpanded_line = (
                        "\t" * tabs + " " * remaining_spaces + line[leading_spaces:]
                    )
                else:
                    unexpanded_line = line
            else:
                # Convert all space sequences
                unexpanded_line = ""
                i = 0
                while i < len(line):
                    if line[i] == " ":
                        # Count consecutive spaces
                        space_count = 0
                        j = i
                        while j < len(line) and line[j] == " ":
                            space_count += 1
                            j += 1

                        if space_count >= tab_size:
                            tabs = space_count // tab_size
                            remaining_spaces = space_count % tab_size
                            unexpanded_line += "\t" * tabs + " " * remaining_spaces
                        else:
                            unexpanded_line += " " * space_count

                        i = j
                    else:
                        unexpanded_line += line[i]
                        i += 1

            result.append(unexpanded_line)

        return "".join(result)

    def _unexpand_with_stops(
        self, content: str, stops: list[int], first_only: bool
    ) -> str:
        """Convert spaces to tabs using custom tab stops."""
        # For simplicity, use the first tab stop as the standard interval
        tab_size = stops[0] if stops else 8
        return self._unexpand_with_size(content, tab_size, first_only)
