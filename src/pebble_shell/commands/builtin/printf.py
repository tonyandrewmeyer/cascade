"""Implementation of PrintfCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PrintfCommand(Command):
    """Command for formatting and printing data."""
    name = "printf"
    help = "Format and print data"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the printf command to format and print data."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print(get_theme().error_text("printf: missing format string"))
            return 1

        format_str = args[0]
        arguments = args[1:]

        try:
            # Process escape sequences
            format_str = format_str.replace("\\n", "\n")
            format_str = format_str.replace("\\t", "\t")
            format_str = format_str.replace("\\\\", "\\")

            # Simple printf implementation
            result = ""
            arg_index = 0
            i = 0

            while i < len(format_str):
                if format_str[i] == "%" and i + 1 < len(format_str):
                    specifier = format_str[i + 1]

                    if specifier == "%":
                        result += "%"
                    elif arg_index < len(arguments):
                        arg = arguments[arg_index]
                        arg_index += 1

                        if specifier == "s":
                            result += str(arg)
                        elif specifier in ("d", "i"):
                            try:
                                result += str(int(arg))
                            except ValueError:
                                result += "0"
                        elif specifier == "o":
                            try:
                                result += oct(int(arg))[2:]
                            except ValueError:
                                result += "0"
                        elif specifier == "x":
                            try:
                                result += hex(int(arg))[2:]
                            except ValueError:
                                result += "0"
                        elif specifier == "X":
                            try:
                                result += hex(int(arg))[2:].upper()
                            except ValueError:
                                result += "0"
                        elif specifier == "f":
                            try:
                                result += str(float(arg))
                            except ValueError:
                                result += "0.0"
                        elif specifier == "c":
                            if arg:
                                result += str(arg)[0]
                        else:
                            result += "%" + specifier
                    else:
                        result += "%" + specifier

                    i += 2
                else:
                    result += format_str[i]
                    i += 1

            print(result, end="")
            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"printf: {e}"))
            return 1
