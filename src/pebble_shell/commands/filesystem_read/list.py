"""List command for Cascade."""

from __future__ import annotations

import posixpath
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
from ...utils.command_helpers import parse_flags
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
        """Execute ls command."""
        # We can't support -h for --help, because -h is for human-readable sizes.
        if "--help" in args:
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
                "t": bool,  # sort by modification time
                "S": bool,  # sort by size
                "r": bool,  # reverse sort order
                "1": bool,  # one entry per line
                "R": bool,  # recursive listing
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, filtered_args = result

        human_readable = flags.get("h", False)
        show_all = flags.get("a", False)
        long_listing = flags.get("l", False)
        sort_by_time = flags.get("t", False)
        sort_by_size = flags.get("S", False)
        reverse_sort = flags.get("r", False)
        one_per_line = flags.get("1", False)
        recursive = flags.get("R", False)

        if filtered_args:
            path = resolve_path(
                self.shell.current_directory, filtered_args[0], self.shell.home_dir
            )
        else:
            path = self.shell.current_directory

        return self._list_directory(
            client,
            path,
            show_all=show_all,
            long_listing=long_listing,
            human_readable=human_readable,
            show_plain=show_plain,
            sort_by_time=sort_by_time,
            sort_by_size=sort_by_size,
            reverse_sort=reverse_sort,
            one_per_line=one_per_line,
            recursive=recursive,
            is_root=True,
        )

    def _list_directory(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        path: str,
        *,
        show_all: bool,
        long_listing: bool,
        human_readable: bool,
        show_plain: bool,
        sort_by_time: bool,
        sort_by_size: bool,
        reverse_sort: bool,
        one_per_line: bool,
        recursive: bool,
        is_root: bool,
    ) -> int:
        """List a single directory, optionally recursing into subdirectories."""
        try:
            files = client.list_files(path)
        except Exception as e:
            self.shell.console.print(f"cannot list directory: {e}")
            return 1

        if not files:
            if recursive and not is_root:
                self.shell.console.print(f"\n{path}:")
            if is_root:
                self.shell.console.print(f"[dim]Directory {path} is empty[/dim]")
            return 0

        if not show_all:
            files = [f for f in files if not f.name.startswith(".")]

        # Sort files
        files = self._sort_files(files, sort_by_time, sort_by_size, reverse_sort)

        # Print header for recursive listings (non-root directories)
        if recursive and not is_root:
            self.shell.console.print(f"\n{path}:")

        # One-per-line mode: plain text output (but -l already implies one-per-line)
        if one_per_line and not long_listing:
            for file_info in files:
                self.shell.console.print(file_info.name)
        else:
            self._print_table(files, long_listing, human_readable, show_plain)

        # Recurse into subdirectories
        exit_code = 0
        if recursive:
            import ops as ops_module

            subdirs = [
                f for f in files if f.type == ops_module.pebble.FileType.DIRECTORY
            ]
            for subdir in subdirs:
                subdir_path = posixpath.join(path, subdir.name)
                result = self._list_directory(
                    client,
                    subdir_path,
                    show_all=show_all,
                    long_listing=long_listing,
                    human_readable=human_readable,
                    show_plain=show_plain,
                    sort_by_time=sort_by_time,
                    sort_by_size=sort_by_size,
                    reverse_sort=reverse_sort,
                    one_per_line=one_per_line,
                    recursive=recursive,
                    is_root=False,
                )
                if result != 0:
                    exit_code = result

        return exit_code

    def _sort_files(
        self,
        files: list[ops.pebble.FileInfo],
        sort_by_time: bool,
        sort_by_size: bool,
        reverse_sort: bool,
    ) -> list[ops.pebble.FileInfo]:
        """Sort files according to flags."""
        if sort_by_time:
            files = sorted(
                files,
                key=lambda f: (
                    f.last_modified.timestamp() if f.last_modified is not None else 0
                ),
                reverse=not reverse_sort,
            )
        elif sort_by_size:
            files = sorted(
                files,
                key=lambda f: f.size if f.size is not None else 0,
                reverse=not reverse_sort,
            )
        else:
            # Default: alphabetical by name (case-sensitive, matching GNU ls)
            files = sorted(files, key=lambda f: f.name, reverse=reverse_sort)
        return files

    def _print_table(
        self,
        files: list[ops.pebble.FileInfo],
        long_listing: bool,
        human_readable: bool,
        show_plain: bool,
    ) -> None:
        """Print files in table format."""
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
