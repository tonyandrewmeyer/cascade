"""Implementation of StopCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class StopCommand(Command):
    """Stop a service."""

    name = "pebble-stop"
    help = "Stop one or more services"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the stop command."""
        if handle_help_flag(self, args):
            return 0

        if validate_min_args(
            self.shell, args, 1, "stop <service-name> [service-name2 ...]"
        ):
            return 1

        try:
            change_id = client.stop_services(args)
        except ops.pebble.APIError as e:
            self.console.print(f"Stop operation failed: {e}")
            return 1

        self.console.print(f"Stop operation initiated with change ID: {change_id}")

        change = client.wait_change(change_id)
        self.console.print(f"Stop operation completed with status: {change.status}")

        if change.status == "Done":
            self.console.print(f"Successfully stopped services: {', '.join(args)}")
        else:
            self.console.print(f"Stop operation failed: {change.err}")
        return 0
