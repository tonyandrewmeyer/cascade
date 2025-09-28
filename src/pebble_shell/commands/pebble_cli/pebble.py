"""Implementation of PebbleCommand."""

from __future__ import annotations

import os
import subprocess

import ops
import shimmer

from ...utils.command_helpers import handle_help_flag
from .._base import Command


class PebbleCommand(Command):
    """Run the local pebble executable with socket path set."""

    name = "pebble"
    help = "Run local pebble executable. Usage: pebble <subcommand> [args...]"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the pebble command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print("Usage: pebble <subcommand> [args...]")
            self.console.print("Examples:")
            self.console.print("  pebble plan")
            self.console.print("  pebble services")
            self.console.print("  pebble logs my-service")
            return 1

        if isinstance(client, ops.pebble.Client):
            env = os.environ.copy()
            assert isinstance(self.shell.client, ops.pebble.Client)
            env["PEBBLE_SOCKET"] = self.shell.client.socket_path
            cmd = ["pebble", *args]  # We assume that pebble is on the PATH.
        elif isinstance(client, shimmer.PebbleCliClient):  # type: ignore
            cmd = [client.pebble_binary, *args]
            env = os.environ.copy()
        else:
            raise ValueError("Invalid client type")

        result = subprocess.run(  # noqa: S603
            cmd,
            env=env,
            capture_output=False,  # Don't capture to allow real-time output.
            text=True,
            check=False,  # Don't raise exception on non-zero exit code.
        )
        return result.returncode
