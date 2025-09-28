"""Implementation of UptimeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    parse_proc_loadavg,
    parse_proc_uptime,
    read_proc_file,
)
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class UptimeCommand(Command):
    """Show system uptime and load average."""

    name = "uptime"
    help = "Show system uptime and load average"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute uptime command."""
        if handle_help_flag(self, args):
            return 0
        try:
            uptime_str: list[str] = []

            # Get RTC time
            rtc_content = read_proc_file(client, "/proc/driver/rtc")
            for line in rtc_content.splitlines():
                if not line.startswith("rtc_time"):
                    continue
                rtc_time = line.split(":", 1)[1].strip()
                uptime_str.append(rtc_time)
                break

            # Get uptime information
            uptime_info = parse_proc_uptime(client)
            uptime_str.append("up")

            uptime_seconds = uptime_info["uptime_seconds"]
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            if days > 0:
                uptime_str.append(f"{days} day{'s' if days != 1 else ''},")
            if hours > 0:
                uptime_str.append(f"{hours} hour{'s' if hours != 1 else ''},")
            uptime_str.append(f"{minutes} minute{'s' if minutes != 1 else ''},")

            # Get load average information
            loadavg_info = parse_proc_loadavg(client)
            load1 = loadavg_info["load_1min"]
            load5 = loadavg_info["load_5min"]
            load15 = loadavg_info["load_15min"]
            uptime_str.append(f"load average: {load1}, {load5}, {load15}")

        except ProcReadError as e:
            self.console.print(f"Error reading system uptime: {e}")
            return 1

        self.console.print(" ".join(uptime_str))
        return 0
