"""Implementation of StringsCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

import ops

from .._base import Command
from pebble_shell.utils.command_helpers import safe_read_file

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the text category.
class StringsCommand(Command):
    """Print printable strings from files."""

    name = "strings"
    help = "Print printable strings from files"
    category = "File"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the strings command."""
        return self._execute_strings(client, args)

    def _execute_strings(self, client: ClientType, args: list[str]) -> int:
        if not args:
            self.console.print("Usage: strings [files...]")
            return 1

        for file_path in args:
            try:
                content = safe_read_file(client, file_path, self.shell)
                if content is not None:
                    # Find printable strings (4+ consecutive printable chars)
                    strings = re.findall(r"[!-~]{4,}", content)
                    for string in strings:
                        self.console.print(string)
            except Exception as e:  # noqa: PERF203  # needed for robust file processing
                self.console.print(f"strings: {file_path}: {e}")
                return 1

        return 0
