"""Remove files and directories command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    import ops
    import shimmer

from ...utils import expand_globs_in_tokens, resolve_path
from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
    validate_min_args,
)
from ...utils.file_ops import (
    remove_file_recursive,
)
from .._base import Command


class RemoveCommand(Command):
    """Remove files and directories."""

    name = "rm"
    help = "Remove files and directories"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute rm command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(
            self.shell, args, 1, "rm [-r] [-f] <file1> [file2...]"
        ):
            return 1

        flags_result = parse_flags(args, {"r": bool, "f": bool}, self.shell)
        if flags_result is None:
            return 1

        flags, remaining_args = flags_result
        force = flags.get("f", False)

        if not remaining_args:
            self.console.print("rm: missing operand")
            return 1

        # Expand globs in file arguments
        expanded_files: list[str] = []
        for file_pattern in remaining_args:
            expanded = expand_globs_in_tokens(
                client, [file_pattern], self.shell.current_directory
            )
            if expanded:
                expanded_files.extend(expanded)
            elif not force:
                self.console.print(f"rm: No files match pattern '{file_pattern}'")
                return 1

        if not expanded_files:
            if not force:
                self.console.print("rm: No files to remove")
                return 1
            return 0

        files = [
            resolve_path(self.shell.current_directory, f, self.shell.home_dir)
            for f in expanded_files
        ]

        exit_code = 0
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Removing files...", total=len(files))
            for file_path in files:
                # Use file_ops utility for remove operation
                success = remove_file_recursive(
                    client, self.console, file_path, force, progress, task
                )
                if not success and not force:
                    exit_code = 1

        return exit_code
