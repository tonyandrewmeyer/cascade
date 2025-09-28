"""Implementation of LogsCommand."""

from __future__ import annotations

import os
import subprocess

import ops
import shimmer

from ...utils.command_helpers import handle_help_flag
from .._base import Command


class LogsCommand(Command):
    """Show service logs from the remote container."""

    name = "pebble-logs"
    help = "Show service logs from the remote container. Usage: pebble-logs [service] [options]"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the logs command."""
        if handle_help_flag(self, args):
            return 0

        if isinstance(client, ops.pebble.Client):
            env = os.environ.copy()
            assert isinstance(self.shell.client, ops.pebble.Client)
            env["PEBBLE_SOCKET"] = self.shell.client.socket_path
            cmd = ["pebble", "logs", *args]
        elif isinstance(client, shimmer.PebbleCliClient):  # type: ignore
            cmd = [client.pebble_binary, "logs", *args]
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
