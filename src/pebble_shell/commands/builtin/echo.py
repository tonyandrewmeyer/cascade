"""Print text."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]

# Escape sequence mapping for -e mode (BusyBox default)
_SIMPLE_ESCAPES = {
    "\\": "\\",
    "a": "\a",
    "b": "\b",
    "e": "\x1b",
    "E": "\x1b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}


def _process_escapes(text: str) -> tuple[str, bool]:
    r"""Process backslash escape sequences in text.

    Returns:
        A tuple of (processed_text, should_stop) where should_stop is True
        if a \\c escape was encountered.
    """
    result = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            next_char = text[i + 1]

            if next_char == "c":
                # \c: produce no further output
                return "".join(result), True

            if next_char in _SIMPLE_ESCAPES:
                result.append(_SIMPLE_ESCAPES[next_char])
                i += 2
                continue

            if next_char == "0":
                # \0nnn: octal value (1-3 octal digits after the 0)
                octal_match = re.match(r"0([0-7]{0,3})", text[i + 1 :])
                if octal_match:
                    octal_str = octal_match.group(1)
                    if octal_str:
                        result.append(chr(int(octal_str, 8)))
                    else:
                        result.append("\0")
                    i += 2 + len(octal_str)
                    continue

            if next_char == "x":
                # \xHH: hex value (1-2 hex digits)
                hex_match = re.match(r"x([0-9a-fA-F]{1,2})", text[i + 1 :])
                if hex_match:
                    hex_str = hex_match.group(1)
                    result.append(chr(int(hex_str, 16)))
                    i += 2 + len(hex_str)
                    continue
                # \x with no valid hex digits: output literally
                result.append("\\")
                i += 1
                continue

            # Unknown escape: output the backslash and character literally
            result.append("\\")
            result.append(next_char)
            i += 2
        else:
            result.append(text[i])
            i += 1

    return "".join(result), False


class EchoCommand(Command):
    """Print text."""

    name = "echo"
    help = "Display text"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute echo command.

        Supports flags (only recognized at the start of arguments):
            -n: Do not output the trailing newline
            -e: Enable interpretation of backslash escapes (default)
            -E: Disable interpretation of backslash escapes

        Flags can be combined (e.g. -neE). Once a non-flag argument is
        encountered, all remaining arguments (including things that look
        like flags) are treated as text.
        """
        if handle_help_flag(self, args):
            return 0

        # Parse flags: only leading args matching -[neE]+ are flags
        no_newline = False
        escape_enabled = True  # BusyBox default: escapes are enabled

        text_start = 0
        for i, arg in enumerate(args):
            if (
                arg.startswith("-")
                and len(arg) > 1
                and all(c in "neE" for c in arg[1:])
            ):
                for c in arg[1:]:
                    if c == "n":
                        no_newline = True
                    elif c == "e":
                        escape_enabled = True
                    elif c == "E":
                        escape_enabled = False
                text_start = i + 1
            else:
                break

        text_args = args[text_start:]

        if not text_args:
            # No text arguments: output empty line (or nothing with -n)
            end = "" if no_newline else "\n"
            self.console.print("", end=end, markup=False, highlight=False)
            return 0

        output = " ".join(text_args)

        if escape_enabled:
            output, should_stop = _process_escapes(output)
            if should_stop:
                # \c means no further output including no trailing newline
                self.console.print(output, end="", markup=False, highlight=False)
                return 0

        end = "" if no_newline else "\n"
        self.console.print(output, end=end, markup=False, highlight=False)
        return 0
