"""Find command for Cascade."""

from __future__ import annotations

import fnmatch
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import shimmer

import ops
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from ...utils import resolve_path
from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command


class FindCommand(Command):
    """Find files matching a pattern."""

    name = "find"
    help = "Find files matching pattern"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute find command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 1, "find <search_path> [pattern]"):
            return 1

        # Process search path
        search_path = resolve_path(
            self.shell.current_directory, args[0], self.shell.home_dir
        )
        pattern = args[1] if len(args) > 1 else "*"

        # Use progress tracking
        exit_code = 0
        with Progress(
            SpinnerColumn(), TextColumn("{task.description}"), transient=True
        ) as progress:
            task = progress.add_task(f"Searching {search_path}...", total=None)
            code = self._find_files(client, search_path, pattern, progress, task)
            if code != 0:
                exit_code = code
        return exit_code

    def _find_files(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        path: str,
        pattern: str,
        progress: Progress,
        task: TaskID,
    ) -> int:
        """Recursively find files matching pattern."""
        try:
            files = client.list_files(path)
        except (ops.pebble.PathError, ops.pebble.APIError) as e:
            self.shell.console.print(f"Error listing files in {path}: {e}")
            return 0
        exit_code = 0
        for file_info in files:
            full_path = os.path.join(path, file_info.name)
            if fnmatch.fnmatch(file_info.name, pattern):
                self.shell.console.print(full_path)
            if file_info.type == ops.pebble.FileType.DIRECTORY:
                progress.update(task, description=f"Searching {full_path}...")
                code = self._find_files(client, full_path, pattern, progress, task)
                if code != 0:
                    exit_code = code
        return exit_code
