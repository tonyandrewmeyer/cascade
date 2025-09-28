"""Find the location of a command on the remote system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class WhichCommand(Command):
    """Find the location of a command on the remote system."""

    name = "which"
    help = "Find the location of a command on the remote system"
    category = "Remote Execution"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute which command."""
        if handle_help_flag(self, args):
            return 0
        if not validate_min_args(self.shell, args, 1, "which <command> [command2...]"):
            return 1

        exit_code = 0
        for command in args:
            found = False
            try:
                # Use the remote 'which' command if available.
                process = client.exec(["which", command])
                stdout, _ = process.wait_output()
                if stdout and stdout.strip():
                    self.console.print(f"{command}: {stdout.strip()}")
                    found = True
            except (ops.pebble.ExecError, ops.pebble.APIError):
                # Fallback: try common paths.
                # TODO: We should really get the PATH from the remote system and use that.
                common_paths = [
                    "/bin/",
                    "/usr/bin/",
                    "/usr/local/bin/",
                    "/sbin/",
                    "/usr/sbin/",
                    "/usr/local/sbin/",
                ]
                for path in common_paths:
                    try:
                        test_process = client.exec(["test", "-x", f"{path}{command}"])
                        test_process.wait()
                        self.console.print(f"{command}: {path}{command}")
                        found = True
                        break
                    except (ops.pebble.ExecError, ops.pebble.APIError):
                        continue

            if not found:
                self.console.print(f"{command}: not found")
                exit_code = 1
        return exit_code
