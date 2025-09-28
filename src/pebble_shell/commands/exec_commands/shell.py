"""Start an interactive shell on the remote system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command
from .exec import ExecCommand

if TYPE_CHECKING:
    import shimmer

# TODO: This doesn't seem to work correctly. Maybe the interactivity needs fixing?

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class ShellCommand(Command):
    """Start an interactive shell on the remote system."""

    name = "shell"
    help = "Start an interactive shell on the remote system"
    category = "Remote Execution"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute shell command."""
        if handle_help_flag(self, args):
            return 0

        # Try to find a suitable shell
        shells = ["/bin/bash", "/bin/sh", "/bin/zsh", "/bin/dash"]

        # If user specified a shell, try that first
        if args:
            shells = [args[0], *shells]

        for shell_path in shells:
            try:
                # Test if the shell exists and is executable
                test_process = client.exec(["test", "-x", shell_path])
                test_process.wait()

                # If we get here, the shell exists, start it
                self.console.print(f"Starting interactive shell: {shell_path}")

                # Start the shell with remaining args
                shell_args = [shell_path, *args[1:]] if args else [shell_path]
                exec_cmd = ExecCommand(self.shell)
                return exec_cmd.execute_remote_command(
                    client, shell_args, interactive=True
                )

            except (ops.pebble.ExecError, ops.pebble.APIError):  # noqa: PERF203  # needed for shell detection
                continue

        self.console.print("No suitable shell found on the remote system")
        return 1
