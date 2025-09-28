"""Copy files and directories command."""

from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING

import ops
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    import shimmer

from ...utils import expand_globs_in_tokens, resolve_path
from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
    validate_min_args,
)
from ...utils.file_ops import (
    copy_directory_recursive,
    copy_file_with_progress,
    get_file_info,
)
from .._base import Command


class CopyCommand(Command):
    """Copy files and directories."""

    name = "cp"
    help = "Copy files and directories. Usage: cp [-r] <source> <destination> or cp [-r] <source1> [source2...] <directory>"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute cp command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 2, "cp [-r] <source> <destination>"):
            return 1

        flags_result = parse_flags(args, {"r": bool}, self.shell)
        if flags_result is None:
            return 1

        flags, remaining_args = flags_result
        recursive = flags.get("r", False)

        if len(remaining_args) < 2:
            self.console.print("cp: missing file operand")
            return 1

        # Expand globs in source files
        source_files = remaining_args[:-1]
        destination = remaining_args[-1]

        expanded_sources: list[str] = []
        for source in source_files:
            expanded = expand_globs_in_tokens(
                client, [source], self.shell.current_directory
            )
            if expanded:
                expanded_sources.extend(expanded)
            else:
                self.console.print(f"cp: No files match pattern '{source}'")
                return 1

        if not expanded_sources:
            self.console.print("cp: No source files found")
            return 1

        sources = [
            resolve_path(self.shell.current_directory, f, self.shell.home_dir)
            for f in expanded_sources
        ]
        destination = resolve_path(
            self.shell.current_directory, destination, self.shell.home_dir
        )

        # Check if destination is directory
        dest_info = get_file_info(client, destination)
        dest_is_dir = (
            dest_info is not None and dest_info.type == ops.pebble.FileType.DIRECTORY
        )

        if len(sources) > 1 and not dest_is_dir:
            self.console.print("cp: target is not a directory")
            return 1

        exit_code = 0
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Copying files...", total=len(sources))
            for source in sources:
                code = self._copy_item(
                    client, source, destination, dest_is_dir, recursive, progress, task
                )
                if code != 0:
                    exit_code = code

        return exit_code

    def _copy_item(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        source: str,
        dest: str,
        dest_is_dir: bool,
        recursive: bool,
        progress: Progress,
        task_id: int,
    ) -> int:
        """Copy a single item using file_ops utilities."""
        source_info = get_file_info(client, source)
        if source_info is None:
            self.console.print(f"cp: cannot stat '{source}': file not found")
            return 1

        # Determine final destination path
        if dest_is_dir:
            source_name = pathlib.Path(source).name
            final_dest = os.path.join(dest, source_name)
        else:
            final_dest = dest

        if source_info.type == ops.pebble.FileType.FILE:
            success = copy_file_with_progress(
                client, self.console, source, final_dest, progress, task_id
            )
            return 0 if success else 1
        elif source_info.type == ops.pebble.FileType.DIRECTORY:
            if not recursive:
                self.console.print(f"'{source}' is a directory (not copied)")
                return 1
            success = copy_directory_recursive(
                client, self.console, source, final_dest, progress, task_id
            )
            return 0 if success else 1
        else:
            self.console.print(f"'{source}': unsupported file type")
            return 1
