"""Move/rename files and directories command."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import ops
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    import shimmer

from ...utils import resolve_path
from ...utils.command_helpers import (
    handle_help_flag,
    validate_min_args,
)
from ...utils.file_ops import (
    get_file_info,
    move_file_with_progress,
)
from .._base import Command


class MoveCommand(Command):
    """Move/rename files and directories."""

    name = "mv"
    help = "Move/rename files or directories"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute mv command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 2, "mv <source> <destination>"):
            return 1

        sources = [
            resolve_path(self.shell.current_directory, f, self.shell.home_dir)
            for f in args[:-1]
        ]
        destination = resolve_path(
            self.shell.current_directory, args[-1], self.shell.home_dir
        )

        # Check if destination is directory
        dest_info = get_file_info(client, destination)
        dest_is_dir = (
            dest_info is not None and dest_info.type == ops.pebble.FileType.DIRECTORY
        )

        if len(sources) > 1 and not dest_is_dir:
            self.console.print("mv: target is not a directory")
            return 1

        exit_code = 0
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Moving files...", total=len(sources))
            for source in sources:
                code = self._move_item(
                    client, source, destination, dest_is_dir, progress, task
                )
                if code != 0:
                    exit_code = code

        return exit_code

    def _move_item(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        source: str,
        dest: str,
        dest_is_dir: bool,
        progress: Progress,
        task_id: int,
    ) -> int:
        """Move a single item using file_ops utilities."""
        # Determine final destination path
        if dest_is_dir:
            source_name = os.path.basename(source)
            final_dest = os.path.join(dest, source_name)
        else:
            final_dest = dest

        # Use file_ops utility for move operation
        success = move_file_with_progress(
            client, self.console, source, final_dest, progress, task_id
        )
        return 0 if success else 1
