"""Base classes for filesystem read commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    import ops
    import shimmer

from ...utils.command_helpers import (
    format_file_header,
    handle_help_flag,
    parse_lines_argument,
    process_file_arguments,
    safe_read_file_lines,
    validate_min_args,
)
from .._base import Command


class _LinesCommand(Command):
    """Base class for commands that read lines from a file."""

    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute command."""
        if handle_help_flag(self, args):
            return 0

        lines, remaining_args = parse_lines_argument(args)

        if not validate_min_args(self.shell, remaining_args, 1):
            return 1

        file_paths = process_file_arguments(
            self.shell, client, remaining_args, allow_globs=True, min_files=1
        )
        if file_paths is None:
            return 1

        # Process each file
        for file_path in file_paths:
            file_lines = safe_read_file_lines(client, file_path, self.shell)
            if file_lines is None:
                return 1

            # Print filename header if multiple files
            header = format_file_header(file_path, len(file_paths))
            if header:
                self.shell.console.print(header)

            self.process_lines(file_lines, lines)

        return 0

    def process_lines(self, file_lines: Sequence[str], lines: int) -> None:
        """Process lines read from the file."""
        raise NotImplementedError("Subclasses must implement process_lines method")
