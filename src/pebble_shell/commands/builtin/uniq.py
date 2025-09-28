"""Implementation of UniqCommand."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import (
    handle_help_flag,
    safe_read_file,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UniqCommand(Command):
    """Command for reporting or filtering repeated lines in files."""

    name = "uniq"
    help = "Report or filter repeated lines. Usage: uniq [-c] [-d] [-u] [file]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the uniq command to filter or count repeated lines."""
        if handle_help_flag(self, args):
            return 0
        count = False
        only_dup = False
        only_unique = False
        files: list[str] = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "-c":
                count = True
            elif arg == "-d":
                only_dup = True
            elif arg == "-u":
                only_unique = True
            elif arg.startswith("-"):
                self.console.print(f"uniq: invalid option: {arg}")
                return 1
            else:
                files.append(arg)
            i += 1

        if not files:
            self.console.print("uniq: missing file operand")
            return 1

        lines = []
        file_path = (
            files[0]
            if os.path.isabs(files[0])
            else os.path.join(self.shell.current_directory, files[0])
        )
        content = safe_read_file(client, self.shell.error_console, file_path)
        if content is None:
            return 1
        lines = content.splitlines()

        if not lines:
            return 0

        prev: tuple[str, int] | None = None
        count_map: list[tuple[str, int]] = []
        for line in lines:
            if prev is not None and line == prev[0]:
                prev = (prev[0], prev[1] + 1)
            else:
                if prev is not None:
                    count_map.append((prev[0], prev[1]))
                prev = (line, 1)
        if prev is not None:
            count_map.append((prev[0], prev[1]))

        for line, cnt in count_map:
            if only_dup and cnt < 2:
                continue
            if only_unique and cnt > 1:
                continue
            if count:
                print(f"{cnt:7} {line}")
            else:
                print(line)
        return 0
