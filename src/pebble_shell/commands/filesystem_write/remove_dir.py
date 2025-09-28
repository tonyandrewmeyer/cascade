"""Remove empty directories command."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops

if TYPE_CHECKING:
    import shimmer

from ...utils import resolve_path
from ...utils.command_helpers import (
    handle_help_flag,
    validate_min_args,
)
from .._base import Command


class RemoveDirCommand(Command):
    """Remove empty directories."""

    name = "rmdir"
    help = "Remove empty directories"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute rmdir command."""
        if handle_help_flag(self, args):
            self.show_help()
            return 0
        if not validate_min_args(
            self.shell, args, 1, "rmdir <directory1> [directory2...]"
        ):
            return 1

        directories = [
            resolve_path(self.shell.current_directory, d, self.shell.home_dir)
            for d in args
        ]

        exit_code = 0
        for directory in directories:
            try:
                file_info = client.list_files(directory)[0]
            except (ops.pebble.PathError, ops.pebble.APIError):
                self.console.print(f"rmdir: {directory}: No such file or directory")
                exit_code = 1
                continue
            if file_info.type != ops.pebble.FileType.DIRECTORY:
                self.console.print(f"rmdir: {directory}: Not a directory")
                exit_code = 1
                continue

            # Check if empty:
            files = client.list_files(directory)
            if files:
                self.console.print(f"rmdir: {directory}: Directory not empty")
                exit_code = 1
                continue

            # Remove empty directory:
            client.remove_path(directory)
            self.console.print(f"removed directory '{directory}'")
        return exit_code
