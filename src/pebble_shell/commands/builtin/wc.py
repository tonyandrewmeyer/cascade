"""Implementation of WcCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
    process_file_arguments,
    safe_read_file,
    validate_min_args,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class WcCommand(Command):
    """Command for counting lines, words, and characters in files."""
    name = "wc"
    help = "Count lines, words, and characters in files"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the wc command to count text statistics in files."""
        if handle_help_flag(self, args):
            return 0

        flags_result = parse_flags(args, {"l": bool, "w": bool, "c": bool}, self.shell)
        if flags_result is None:
            return 1
        flags, file_args = flags_result

        # Determine what to show based on flags
        any_flag_set = flags["l"] or flags["w"] or flags["c"]
        if any_flag_set:
            # If any flag is set, show only what's requested
            show_lines = flags["l"]
            show_words = flags["w"]
            show_chars = flags["c"]
        else:
            # If no flags set, show all (default behavior)
            show_lines = True
            show_words = True
            show_chars = True

        # Validate file arguments
        if not validate_min_args(
            self.shell, file_args, 1, "wc [-l|-w|-c] <file> [file2...]"
        ):
            return 1

        # Process file arguments
        file_paths = process_file_arguments(
            self.shell, client, file_args, allow_globs=False, min_files=1
        )
        if file_paths is None:
            return 1

        total_lines = 0
        total_words = 0
        total_chars = 0
        show_totals = len(file_paths) > 1

        for file_path in file_paths:
            content = safe_read_file(client, file_path, self.shell)
            if content is None:
                continue

            lines = len(content.splitlines())
            words = len(content.split())
            chars = len(content)

            total_lines += lines
            total_words += words
            total_chars += chars

            output_parts: list[str] = []
            if show_lines:
                output_parts.append(f"{lines:8}")
            if show_words:
                output_parts.append(f"{words:8}")
            if show_chars:
                output_parts.append(f"{chars:8}")

            output = " ".join(output_parts)
            self.console.print(f"{output} {file_path}")

        # Show totals if multiple files
        if show_totals:
            total_output_parts: list[str] = []
            if show_lines:
                total_output_parts.append(f"{total_lines:8}")
            if show_words:
                total_output_parts.append(f"{total_words:8}")
            if show_chars:
                total_output_parts.append(f"{total_chars:8}")

            total_output = " ".join(total_output_parts)
            self.console.print(f"{total_output} total")

        return 0
