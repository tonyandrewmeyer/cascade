"""Right now (rn) command for Cascade.

This module provides implementation for the rn command that displays
the current time, date, and calendar.
"""

from __future__ import annotations

import calendar
import datetime
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class RnCommand(Command):
    """Display current time, date, and calendar."""

    name = "rn"
    help = "Display current time, date, and calendar (right now)"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Display current time, date, and calendar.

Usage: rn [OPTIONS]

Options:
    -h, --help      Show this help message
    -t, --time-only Only show time
    -d, --date-only Only show date
    -c, --cal-only  Only show calendar
    -n, --no-cal    Don't show calendar

Shows the current time, date, and a calendar for the current month
with today highlighted.

Examples:
    rn              # Show time, date, and calendar
    rn -t           # Just the time
    rn -d           # Just the date
    rn -n           # Time and date without calendar
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the rn command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "t": bool,
                "time-only": bool,
                "d": bool,
                "date-only": bool,
                "c": bool,
                "cal-only": bool,
                "n": bool,
                "no-cal": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        time_only = flags["t"] or flags["time-only"]
        date_only = flags["d"] or flags["date-only"]
        cal_only = flags["c"] or flags["cal-only"]
        no_cal = flags["n"] or flags["no-cal"]

        now = datetime.datetime.now()

        if time_only:
            self.console.print(now.strftime("%H:%M:%S"))
            return 0

        if date_only:
            self.console.print(now.strftime("%A, %B %d, %Y"))
            return 0

        if cal_only:
            self._print_calendar(now)
            return 0

        # Full output: time, date, and optionally calendar
        self.console.print(f"[bold cyan]{now.strftime('%H:%M:%S')}[/bold cyan]")
        self.console.print(f"[cyan]{now.strftime('%A, %B %d, %Y')}[/cyan]")

        if not no_cal:
            self.console.print()
            self._print_calendar(now)

        return 0

    def _print_calendar(self, now: datetime.datetime):
        """Print a calendar for the current month with today highlighted."""
        year = now.year
        month = now.month
        today = now.day

        # Get calendar for the month
        cal = calendar.TextCalendar(calendar.SUNDAY)

        # Print month/year header
        month_name = calendar.month_name[month]
        header = f"{month_name} {year}"
        self.console.print(f"[bold]{header:^20}[/bold]")

        # Print day headers
        self.console.print("[dim]Su Mo Tu We Th Fr Sa[/dim]")

        # Print weeks
        for week in cal.monthdayscalendar(year, month):
            week_str = ""
            for day in week:
                if day == 0:
                    week_str += "   "
                elif day == today:
                    week_str += f"[bold reverse]{day:2}[/bold reverse] "
                else:
                    week_str += f"{day:2} "
            self.console.print(week_str.rstrip())
