"""Implementation of WatchCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class WatchCommand(Command):
    """Execute a command repeatedly and display the output."""

    name = "watch"
    help = "Execute a command repeatedly"
    category = "Built-in Commands"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the watch command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 1, "watch <command> [args...]"):
            return 1

        # Parse watch options
        interval = 2.0  # Default 2 second interval
        args_start = 0

        if args and args[0] == "-n":
            if len(args) < 3:
                self.console.print("[red]watch: option requires an argument -- n[/red]")
                return 1
            try:
                interval = float(args[1])
                args_start = 2
            except ValueError:
                self.console.print(f"[red]watch: invalid interval '{args[1]}'[/red]")
                return 1

        if args_start >= len(args):
            self.console.print("[red]watch: no command specified[/red]")
            return 1

        command_args = args[args_start:]

        try:
            iteration = 0
            while True:
                # Clear screen equivalent for console
                self.console.clear()

                # Show header
                self.console.print(
                    f"Every {interval}s: {' '.join(command_args)}    "
                    f"Iteration: {iteration}"
                )
                self.console.print()

                # Execute the command
                from .. import get_command_by_name

                command_name = command_args[0]
                command_class = get_command_by_name(command_name)

                if command_class:
                    command_instance = command_class(self.shell)
                    command_instance.execute(client, command_args[1:])
                else:
                    self.console.print(f"[red]Command not found: {command_name}[/red]")

                self.console.print("-" * 80)
                time.sleep(interval)

        except KeyboardInterrupt:
            self.console.print("\nStopped watching.")
            return 0
