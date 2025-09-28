"""Implementation of GrepCommand."""

from __future__ import annotations

import re
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


class GrepCommand(Command):
    """Command for searching patterns in files using regex or string matching."""
    name = "grep"
    help = "Search for pattern in files"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the grep command to search for patterns in files."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(
            self.shell, args, 2, "grep <pattern> <file> [file2...]"
        ):
            return 1

        pattern = args[0]
        file_args = args[1:]

        file_paths = process_file_arguments(
            self.shell, client, file_args, allow_globs=False, min_files=1
        )
        if file_paths is None:
            return 1

        try:
            if pattern.startswith("/") and pattern.endswith("/"):
                # Regex pattern
                regex = re.compile(pattern[1:-1])
            else:
                # Simple string search (escape special chars)
                regex = re.compile(re.escape(pattern))
        except re.error as e:
            self.console.print(f"grep: invalid pattern: {e}")
            return 1

        total_matches = 0
        show_filename = len(file_paths) > 1

        for file_path in file_paths:
            content = safe_read_file(client, file_path, self.shell)
            if content is None:
                continue

            lines = content.splitlines()
            file_matches = 0

            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    file_matches += 1
                    if show_filename:
                        self.console.print(f"{file_path}:{line_num}:{line}")
                    else:
                        self.console.print(f"{line_num}:{line}")

            total_matches += file_matches

        if total_matches == 0:
            return 1

        return 0
