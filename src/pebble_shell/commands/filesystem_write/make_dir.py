"""Create directories command."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops

if TYPE_CHECKING:
    import shimmer

from ...utils import resolve_path
from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
    validate_min_args,
)
from .._base import Command


class MakeDirCommand(Command):
    """Create directories."""

    name = "mkdir"
    help = "Create directories"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute mkdir command."""
        if handle_help_flag(self, args):
            self.show_help()
            return 0
        if not validate_min_args(
            self.shell, args, 1, "mkdir [-p] <directory1> [directory2...]"
        ):
            return 1

        make_parents = False
        directories: list[str] = []

        # Parse options:
        result = parse_flags(args, {"p": bool}, self.shell)
        if result is None:
            return 1
        flags, directories = result
        make_parents = flags.get("p", False)

        if not directories:
            self.console.print("mkdir: missing operand")
            return 1

        directories = [
            resolve_path(self.shell.current_directory, d, self.shell.home_dir)
            for d in directories
        ]

        exit_code = 0
        for directory in directories:
            try:
                client.make_dir(directory, make_parents=make_parents)
            except ops.pebble.PathError:  # noqa: PERF203
                self.console.print(f"mkdir: {directory}: No such file or directory")
                exit_code = 1
            else:
                self.console.print(f"created directory '{directory}'")
        return exit_code
