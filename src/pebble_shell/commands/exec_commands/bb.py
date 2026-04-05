"""Background command execution for Cascade.

bb (background) runs a command on the remote system without waiting
for it to complete.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class BbCommand(Command):
    """Run a command in the background."""

    name = "bb"
    help = "Run a command in the background"
    category = "Remote Execution"

    def show_help(self):
        """Show command help."""
        help_text = """Run a command in the background.

Usage: bb [OPTIONS] COMMAND [ARGS...]

Options:
    -h, --help      Show this help message
    -q, --quiet     Don't show confirmation message

Arguments:
    COMMAND         Command to run
    ARGS            Arguments to pass to the command

Runs the command on the remote system without waiting for it to complete.
The command runs detached with no stdin/stdout/stderr connection.

Examples:
    bb sleep 60                 # Run sleep in background
    bb ./long-running-script    # Start a long script
    bb -q cleanup.sh            # Run quietly without message
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the bb command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "q": bool,
                "quiet": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, command_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if not command_args:
            self.console.print("[red]bb: missing command[/red]")
            self.console.print("Usage: bb <command> [args...]")
            return 1

        quiet = flags["q"] or flags["quiet"]

        try:
            # Run detached - don't connect stdin/stdout/stderr and don't wait
            client.exec(
                command_args,
                stdin=None,
                stdout=None,
                stderr=None,
            )

            if not quiet:
                cmd_str = " ".join(command_args)
                self.console.print(f"[green]Started in background:[/green] {cmd_str}")

            return 0

        except ops.pebble.APIError as e:
            self.console.print(f"[red]bb: failed to start command: {e}[/red]")
            return 1
        except ops.pebble.ExecError as e:
            self.console.print(f"[red]bb: command failed: {e}[/red]")
            return 1
