"""Implementation of CalCommand."""

from __future__ import annotations

import calendar
import datetime
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Is this really the right group?
class CalCommand(Command):
    """Implementation of cal command."""

    name = "cal"
    help = "Display calendar"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the cal command."""
        if handle_help_flag(self, args):
            return 0

        now = datetime.datetime.now()
        year = now.year
        month = now.month

        if len(args) == 1:
            # Could be year or month
            try:
                arg = int(args[0])
                if arg > 12:
                    # Probably a year
                    year = arg
                    # Show entire year
                    cal_text = calendar.calendar(year)
                    self.console.print(cal_text)
                    return 0
                else:
                    # Month for current year
                    month = arg
            except ValueError:
                self.console.print(get_theme().error_text("cal: invalid number"))
                return 1
        elif len(args) == 2:
            try:
                month = int(args[0])
                year = int(args[1])
            except ValueError:
                self.console.print(get_theme().error_text("cal: invalid number"))
                return 1

        if month < 1 or month > 12:
            self.console.print(get_theme().error_text("cal: invalid month"))
            return 1

        try:
            cal_text = calendar.month(year, month)
            self.console.print(cal_text)
            return 0
        except Exception as e:
            self.console.print(get_theme().error_text(f"cal: {e}"))
            return 1
