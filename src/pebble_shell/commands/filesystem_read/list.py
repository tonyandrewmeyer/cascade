"""List command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ops
    import shimmer

from ...utils import (
    format_bytes,
    format_file_info,
    format_relative_time,
    resolve_path,
)
from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.table_builder import add_file_columns, create_standard_table
from .._base import Command


class ListCommand(Command):
    """List directory contents."""

    name = "ls"
    help = "List directory contents"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute ls command with rich table output, relative times, icons/emojis, -h for human sizes, -a for dot files, and -l for long listing."""
        # We can't support -h for --help, because -h is for human-readable sizes.
        if handle_help_flag(self, args):
            self.show_help()
            return 0

        # Handle special flags first
        show_plain = "--plain-timestamp" in args
        if show_plain:
            args = [arg for arg in args if arg != "--plain-timestamp"]

        result = parse_flags(
            args,
            {
                "h": bool,  # human-readable sizes
                "a": bool,  # show all (including dot files)
                "l": bool,  # long listing
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, filtered_args = result

        human_readable = flags.get("h", False)
        show_all = flags.get("a", False)
        long_listing = flags.get("l", False)

        if filtered_args:
            path = resolve_path(
                self.shell.current_directory, filtered_args[0], self.shell.home_dir
            )
        else:
            path = self.shell.current_directory

        try:
            files = client.list_files(path)
        except Exception as e:
            self.shell.console.print(f"cannot list directory: {e}")
            return 1

        if not files:
            self.shell.console.print(f"[dim]Directory {path} is empty[/dim]")
            return 0

        if not show_all:
            files = [f for f in files if not f.name.startswith(".")]

        table_builder = create_standard_table()
        if long_listing:
            table = add_file_columns(table_builder, long_format=True).build()
        else:
            if human_readable:
                table = (
                    table_builder.numeric_column("Size")
                    .data_column("Name", no_wrap=False)
                    .build()
                )
            else:
                table = table_builder.data_column("Name", no_wrap=False).build()

        for file_info in files:
            permissions = format_file_info(file_info)[0:10]
            owner = str(file_info.user_id) if file_info.user_id is not None else "0"
            group = str(file_info.group_id) if file_info.group_id is not None else "0"

            if file_info.size is not None:
                size_str = (
                    format_bytes(file_info.size)
                    if human_readable
                    else str(file_info.size)
                )
            else:
                size_str = "0"

            if file_info.last_modified:
                if show_plain:
                    time_str = file_info.last_modified.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    time_str = format_relative_time(file_info.last_modified)
            else:
                time_str = "unknown"

            if long_listing:
                table.add_row(
                    permissions,
                    owner,
                    group,
                    size_str,
                    time_str,
                    file_info.name,
                )
            else:
                if human_readable:
                    table.add_row(size_str, file_info.name)
                else:
                    table.add_row(file_info.name)

        self.shell.console.print(table)
        return 0
