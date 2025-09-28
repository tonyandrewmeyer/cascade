"""Create empty files or update timestamps command."""

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


class TouchCommand(Command):
    """Create empty files or update timestamps."""

    name = "touch"
    help = "Create empty files or update timestamps"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute touch command."""
        if handle_help_flag(self, args):
            self.show_help()
            return 0
        if not validate_min_args(self.shell, args, 1, "touch <file1> [file2...]"):
            return 1

        file_paths = [
            resolve_path(self.shell.current_directory, f, self.shell.home_dir)
            for f in args
        ]

        for file_path in file_paths:
            try:
                file_info = client.list_files(file_path)[0]
                if file_info.type == ops.pebble.FileType.DIRECTORY:
                    self.console.print(f"touch: {file_path}: Is a directory")
                    continue
                # We have to pull and then push the same content.
                with client.pull(file_path) as f:
                    content = f.read()
                client.push(file_path, content)
                self.console.print(f"touched '{file_path}' (file existed)")
            except (ops.pebble.PathError, ops.pebble.APIError):
                client.push(file_path, b"", make_dirs=True)
                self.console.print(f"created '{file_path}'")
        return 0
