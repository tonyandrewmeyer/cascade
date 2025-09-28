"""Implementation of SignalCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class SignalCommand(Command):
    """Send a signal to a service."""

    name = "pebble-signal"
    help = "Send a signal to services"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the signal command."""
        if handle_help_flag(self, args):
            return 0

        if len(args) < 2:
            self.console.print(
                "Usage: signal <signal> <service-name> [service-name2 ...]"
            )
            self.console.print(
                "Common signals: SIGTERM, SIGKILL, SIGHUP, SIGUSR1, SIGUSR2"
            )
            return 1

        signal_name = args[0]
        service_names = args[1:]

        try:
            client.send_signal(signal_name, service_names)
        except ops.pebble.APIError as e:
            self.console.print(f"Signal operation failed: {e}")
            return 1

        self.console.print(
            f"Successfully sent {signal_name} to services: {', '.join(service_names)}"
        )

        return 0
