"""Implementation of StartChecksCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops

from ...utils.command_helpers import handle_help_flag, validate_min_args
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class StartChecksCommand(Command):
    """Start health checks."""

    name = "pebble-start-checks"
    help = "Start one or more health checks"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the start-checks command."""
        if handle_help_flag(self, args):
            return 0

        if validate_min_args(
            self.shell, args, 1, "start-checks <check-name> [check-name2 ...]"
        ):
            return 1

        try:
            changed_checks = client.start_checks(args)
        except ops.pebble.APIError as e:
            self.console.print(f"Start checks operation failed: {e}")
            return 1

        self.console.print(f"Started checks: {', '.join(changed_checks)}")

        return 0
