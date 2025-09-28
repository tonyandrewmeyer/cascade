"""Fold command for Cascade.

This module provides implementation for the fold command that wraps
text to specified width.
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


class FoldCommand(Command):
    """Implementation of fold command."""

    name = "fold"
    help = "Wrap text to specified width"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the fold command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "w": str,  # width
                "b": bool,  # count bytes instead of columns
                "s": bool,  # break at spaces
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        width = int(flags.get("w", "80"))
        count_bytes = flags.get("b", False)
        break_at_spaces = flags.get("s", False)

        try:
            if not positional_args:
                self.console.print(
                    get_theme().warning_text("fold: reading from stdin not supported")
                )
                return 1

            for file_path in positional_args:
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    return 1

                folded = self._fold_text(content, width, count_bytes, break_at_spaces)
                self.console.print(folded, end="")

            return 0

        except (ValueError, TextUtilsError) as e:
            self.console.print(get_theme().error_text(f"fold: {e}"))
            return 1

    def _fold_text(
        self, content: str, width: int, count_bytes: bool, break_at_spaces: bool
    ) -> str:
        """Fold text to specified width."""
        lines = content.splitlines(keepends=True)
        result = []

        for line in lines:
            if line.endswith("\n"):
                line_content = line[:-1]
                newline = "\n"
            else:
                line_content = line
                newline = ""

            if len(line_content) <= width:
                result.append(line)
                continue

            if break_at_spaces:
                # Break at spaces when possible
                words = line_content.split(" ")
                current_line = ""

                for word in words:
                    if not current_line:
                        current_line = word
                    elif len(current_line) + 1 + len(word) <= width:
                        current_line += " " + word
                    else:
                        result.append(current_line + "\n")
                        current_line = word

                if current_line:
                    result.append(current_line + newline)
            else:
                # Break at exact width
                i = 0
                while i < len(line_content):
                    chunk = line_content[i : i + width]
                    i += width

                    if i >= len(line_content):
                        result.append(chunk + newline)
                    else:
                        result.append(chunk + "\n")

        return "".join(result)
