"""Implementation of DuCommand."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import ops

from ...utils import format_bytes, resolve_path
from ...utils.command_helpers import handle_help_flag
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class DuCommand(Command):
    """Show disk usage of files and directories."""

    name = "du"
    help = "Show disk usage. Use -h for human-readable sizes, -s for summary only"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute du command with rich table output."""
        if handle_help_flag(self, args):
            return 0
        human_readable = False
        summary_only = False
        paths: list[str] = []

        for arg in args:
            if arg == "-h":
                human_readable = True
            elif arg == "-s":
                summary_only = True
            else:
                paths.append(arg)

        if not paths:
            paths = ["."]

        table = create_enhanced_table()
        table.add_column("Size", style="yellow", justify="right")
        table.add_column("Path", style="green")

        total_size = 0

        for path in paths:
            resolved_path = resolve_path(
                self.shell.current_directory, path, home_dir=self.shell.home_dir
            )
            size = self._calculate_size(client, resolved_path, summary_only)
            total_size += size

            size_str = format_bytes(size) if human_readable else str(size)

            table.add_row(
                f"[yellow]{size_str}[/yellow]",
                f"[green]{resolved_path}[/green]",
            )

        self.console.print(table.build())

        if len(paths) > 1:
            total_str = format_bytes(total_size) if human_readable else str(total_size)
            self.console.print(f"[bold]Total: {total_str}[/bold]")
        return 0

    def _calculate_size(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        path: str,
        summary_only: bool,
    ) -> int:
        """Calculate the size of a file or directory."""
        parent_dir = os.path.dirname(path)
        filename = os.path.basename(path)

        if parent_dir == "":
            parent_dir = "/"

        files = client.list_files(parent_dir)
        for file_info in files:
            if file_info.name == filename:
                if file_info.type == ops.pebble.FileType.FILE:
                    return file_info.size or 0
                if file_info.type == ops.pebble.FileType.DIRECTORY:
                    return self._calculate_directory_size(client, path)
                return 0

        return 0

    def _calculate_directory_size(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, path: str
    ) -> int:
        """Calculate the total size of a directory recursively."""
        total_size = 0
        files = client.list_files(path)
        for file_info in files:
            file_path = f"{path}/{file_info.name}"
            if file_info.type == ops.pebble.FileType.FILE:
                total_size += file_info.size or 0
            elif file_info.type == ops.pebble.FileType.DIRECTORY:
                total_size += self._calculate_directory_size(client, file_path)
        return total_size
