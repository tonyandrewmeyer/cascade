"""Implementation of PushCommand."""

from __future__ import annotations

import os
import subprocess

import ops
import shimmer

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command


class PushCommand(Command):
    """Push files and directories to the remote container."""

    name = "push"
    help = "Push files and directories to the remote container. Usage: pebble push <source> <dest>"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the push command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(
            self.shell, args, 2, "Usage: pebble push <source> <dest>"
        ):
            return 1

        source = args[0]
        dest = args[1]

        if isinstance(client, ops.pebble.Client):
            env = os.environ.copy()
            assert isinstance(self.shell.client, ops.pebble.Client)
            env["PEBBLE_SOCKET"] = self.shell.client.socket_path
            cmd = ["pebble", "push", source, dest]
        elif isinstance(client, shimmer.PebbleCliClient):  # type: ignore
            cmd = [client.pebble_binary, "push", source, dest]
        else:
            self.console.print("Error: unsupported client type")
            return 1

        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=False,
            text=True,
            env=env if isinstance(client, ops.pebble.Client) else None,
        )
        return result.returncode
