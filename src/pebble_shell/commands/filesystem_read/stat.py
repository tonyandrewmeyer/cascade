"""Stat command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ops
    import shimmer

from ...utils import format_stat_info
from ...utils.command_helpers import (
    handle_help_flag,
    process_file_arguments,
    validate_min_args,
)
from .._base import Command


class StatCommand(Command):
    """Show file/directory statistics."""

    name = "stat"
    help = "Show file/directory statistics"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute stat command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 1, "stat <file>"):
            return 1

        file_paths = process_file_arguments(
            self.shell, client, args, allow_globs=True, min_files=1
        )
        if file_paths is None:
            return 1

        # Process each file
        for file_path in file_paths:
            try:
                # Get the directory containing the file
                dir_path = file_path.rsplit("/", 1)[0] if "/" in file_path else "."
                file_name = (
                    file_path.rsplit("/", 1)[1] if "/" in file_path else file_path
                )

                files = client.list_files(dir_path)
                for file_info in files:
                    if file_info.name == file_name:
                        self.shell.console.print(format_stat_info(file_info, file_path))
                        break
                else:
                    self.shell.console.print(f"Error: File {file_path} not found")
                    return 1

            except Exception as e:
                self.shell.console.print(
                    f"Error getting file info for {file_path}: {e}"
                )
                return 1

        return 0
