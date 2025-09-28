"""Expand command for Cascade.

This module provides implementation for the expand command that converts
tabs to spaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Move this to an exceptions.py module.
class TextUtilsError(Exception):
    """Exception raised for text processing errors."""


class ExpandCommand(Command):
    """Implementation of expand command."""

    name = "expand"
    help = "Convert tabs to spaces"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the expand command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "t": str,  # tab stops
                "i": bool,  # initial tabs only
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        tab_stops = flags.get("t", "8")
        initial_only = flags.get("i", False)

        try:
            if "," in tab_stops:
                stops = [int(x) for x in tab_stops.split(",")]
            else:
                tab_size = int(tab_stops)
                stops = None

            if not positional_args:
                self.console.print(
                    get_theme().warning_text("expand: reading from stdin not supported")
                )
                return 1

            for file_path in positional_args:
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    return 1

                if stops:
                    expanded = self._expand_with_stops(content, stops, initial_only)
                else:
                    expanded = self._expand_with_size(content, tab_size, initial_only)

                self.console.print(expanded, end="")

            return 0

        except (ValueError, TextUtilsError) as e:
            self.console.print(get_theme().error_text(f"expand: {e}"))
            return 1

    def _expand_with_size(self, content: str, tab_size: int, initial_only: bool) -> str:
        """Expand tabs using a fixed tab size."""
        lines = content.splitlines(keepends=True)
        result = []

        for line in lines:
            if initial_only:
                # Only expand leading tabs
                leading_tabs = 0
                for char in line:
                    if char == "\t":
                        leading_tabs += 1
                    elif char != " ":
                        break

                if leading_tabs > 0:
                    spaces = " " * (leading_tabs * tab_size)
                    expanded_line = spaces + line[leading_tabs:]
                else:
                    expanded_line = line
            else:
                # Expand all tabs
                expanded_line = ""
                col = 0
                for char in line:
                    if char == "\t":
                        spaces_needed = tab_size - (col % tab_size)
                        expanded_line += " " * spaces_needed
                        col += spaces_needed
                    else:
                        expanded_line += char
                        if char == "\n":
                            col = 0
                        else:
                            col += 1

            result.append(expanded_line)

        return "".join(result)

    def _expand_with_stops(
        self, content: str, stops: list[int], initial_only: bool
    ) -> str:
        """Expand tabs using custom tab stops."""
        lines = content.splitlines(keepends=True)
        result = []

        for line in lines:
            if initial_only:
                # Only expand leading tabs
                expanded_line = ""
                col = 0
                initial = True

                for char in line:
                    if char == "\t" and initial:
                        # Find next tab stop
                        next_stop = None
                        for stop in stops:
                            if stop > col:
                                next_stop = stop
                                break

                        if next_stop:
                            spaces_needed = next_stop - col
                            expanded_line += " " * spaces_needed
                            col = next_stop
                        else:
                            # No more stops, use last stop as interval
                            interval = stops[-1] - stops[-2] if len(stops) > 1 else 8
                            next_pos = col + interval
                            spaces_needed = next_pos - col
                            expanded_line += " " * spaces_needed
                            col = next_pos
                    else:
                        if char != " " and char != "\t":
                            initial = False
                        expanded_line += char
                        if char == "\n":
                            col = 0
                            initial = True
                        else:
                            col += 1
            else:
                # Expand all tabs
                expanded_line = ""
                col = 0

                for char in line:
                    if char == "\t":
                        # Find next tab stop
                        next_stop = None
                        for stop in stops:
                            if stop > col:
                                next_stop = stop
                                break

                        if next_stop:
                            spaces_needed = next_stop - col
                            expanded_line += " " * spaces_needed
                            col = next_stop
                        else:
                            # No more stops, use default behavior
                            interval = 8
                            next_pos = ((col // interval) + 1) * interval
                            spaces_needed = next_pos - col
                            expanded_line += " " * spaces_needed
                            col = next_pos
                    else:
                        expanded_line += char
                        if char == "\n":
                            col = 0
                        else:
                            col += 1

            result.append(expanded_line)

        return "".join(result)
