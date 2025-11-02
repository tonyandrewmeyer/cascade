"""Implementation of PebbleCommand."""

from __future__ import annotations

import os
import subprocess

import ops
import shimmer

from ...utils.command_helpers import handle_help_flag
from .._base import Command


class PebbleCommand(Command):
    """Pebble command dispatcher for subcommands."""

    name = "pebble"
    help = "Pebble command dispatcher. Usage: pebble <subcommand> [args...]"
    category = "Pebble Management"

    # Map of subcommand names to their command instances
    _subcommands = None

    def _init_subcommands(self):
        """Initialize the subcommand mapping from shell commands."""
        if self._subcommands is None:
            PebbleCommand._subcommands = {}
            # Get all commands from the shell that are pebble subcommands
            for cmd_name, cmd_instance in self.shell.commands.items():
                # Look for commands that belong to pebble_cli package
                if hasattr(cmd_instance, '__module__') and 'pebble_cli' in cmd_instance.__module__:
                    # Skip the pebble command itself
                    if cmd_name != 'pebble':
                        PebbleCommand._subcommands[cmd_name] = cmd_instance

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the pebble command or dispatch to subcommand."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self._show_usage()
            return 1

        # Initialize subcommands if needed
        self._init_subcommands()

        subcommand = args[0]
        subcommand_args = args[1:]

        # Check if this is a known subcommand
        if subcommand in self._subcommands:
            # Dispatch to the appropriate subcommand
            cmd_instance = self._subcommands[subcommand]
            return cmd_instance.execute(client, subcommand_args)

        # If not a known subcommand, try to run the actual pebble binary
        # This allows for pebble commands that aren't implemented in Cascade
        return self._run_pebble_binary(client, args)

    def _run_pebble_binary(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Run the actual pebble binary."""
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

    def _show_usage(self):
        """Show usage information for pebble command."""
        self.console.print("Usage: pebble <subcommand> [args...]")
        self.console.print()
        if self._subcommands:
            self.console.print("Available subcommands:")
            for subcmd in sorted(self._subcommands.keys()):
                cmd_instance = self._subcommands[subcmd]
                help_text = getattr(cmd_instance, 'help', 'No description available')
                # Remove the "pebble-" prefix from help text if present
                help_text = help_text.replace('pebble-', '')
                self.console.print(f"  {subcmd:20} {help_text}")
        else:
            self.console.print("Examples:")
            self.console.print("  pebble plan")
            self.console.print("  pebble services")
            self.console.print("  pebble logs my-service")
