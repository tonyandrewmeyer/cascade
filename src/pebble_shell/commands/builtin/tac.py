"""Implementation of TacCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import (
    handle_help_flag,
    process_file_arguments,
    safe_read_file,
    validate_min_args,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TacCommand(Command):
    """Command for concatenating and printing files in reverse line order."""

    name = "tac"
    help = "Concatenate and print files in reverse"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the tac command to display files in reverse line order."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 1, "tac [file ...]"):
            return 1

        file_paths = process_file_arguments(
            self.shell, client, args, allow_globs=False, min_files=1
        )
        if file_paths is None:
            return 1

        exit_code = 0
        for file_path in file_paths:
            content = safe_read_file(client, file_path, self.shell)
            if content is None:
                exit_code = 1
                continue

            lines = content.splitlines()
            for line in reversed(lines):
                self.console.print(line)
        return exit_code
