"""Implementation of SortCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils import resolve_path
from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
    safe_read_file,
    validate_min_args,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class SortCommand(Command):
    """Command for sorting lines in files."""

    name = "sort"
    help = "Sort lines in files"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the sort command to sort lines in files."""
        if handle_help_flag(self, args):
            return 0

        flags_result = parse_flags(args, {"r": bool, "n": bool, "k": int}, self.shell)
        if flags_result is None:
            return 1
        flags, file_args = flags_result

        if not validate_min_args(
            self.shell, file_args, 1, "sort [-r] [-n] [-k field] <file> [file2...]"
        ):
            return 1

        reverse = flags["r"]
        numeric = flags["n"]
        key_field = flags["k"]
        if key_field is not None:
            key_field -= 1  # Convert to 0-based indexing

        files = file_args

        all_lines: list[str] = []

        for file_path in files:
            resolved_path = resolve_path(
                self.shell.current_directory, file_path, self.shell.home_dir
            )

            content = safe_read_file(client, resolved_path, self.shell)
            if content is None:
                continue

            lines = content.splitlines()
            all_lines.extend(lines)

        if not all_lines:
            return 1

        if key_field is not None:
            # Sort by specific field
            def sort_key(line: str):
                fields = line.split()
                assert key_field is not None  # Type narrowing
                if key_field < len(fields):
                    field_value = fields[key_field]
                    if numeric:
                        try:
                            return float(field_value)
                        except ValueError:
                            return 0
                    return field_value
                return ""

            all_lines.sort(key=sort_key, reverse=reverse)
        elif numeric:
            # Numeric sort
            def numeric_key(line: str):
                try:
                    return float(line.split()[0] if line.split() else "0")
                except (ValueError, IndexError):
                    return 0

            all_lines.sort(key=numeric_key, reverse=reverse)
        else:
            # Alphabetic sort
            all_lines.sort(reverse=reverse)

        # Output sorted lines
        for line in all_lines:
            self.console.print(line)
        return 0
