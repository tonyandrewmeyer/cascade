"""Implementation of usleep command."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UsleepCommand(Command):
    """Implementation of usleep command."""

    name = "usleep"
    help = "Sleep for microseconds"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the usleep command."""
        if handle_help_flag(self, args):
            return 0

        if len(args) != 1:
            self.console.print(get_theme().error_text("usleep: missing operand"))
            return 1

        try:
            microseconds = int(args[0])
            if microseconds < 0:
                self.console.print(
                    get_theme().error_text("usleep: invalid time interval")
                )
                return 1

            time.sleep(microseconds / 1000000.0)
            return 0

        except ValueError:
            self.console.print(get_theme().error_text("usleep: invalid time interval"))
            return 1
        except KeyboardInterrupt:
            return 1
