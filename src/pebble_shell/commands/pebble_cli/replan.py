"""Implementation of ReplanCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class ReplanCommand(Command):
    """Replan services."""

    name = "replan"
    help = "Replan services based on current configuration"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the replan command."""
        if handle_help_flag(self, args):
            return 0

        change_id = client.replan_services()
        self.console.print(f"Replan initiated with change ID: {change_id}")
        change = client.wait_change(change_id)
        self.console.print(f"Replan completed with status: {change.status}")
        return 0
