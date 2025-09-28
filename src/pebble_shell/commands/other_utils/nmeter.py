"""Implementation of NmeterCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the system category.
class NmeterCommand(Command):
    """Implementation of nmeter command."""

    name = "nmeter"
    help = "Display system statistics"
    category = "System Info"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the nmeter command."""
        if handle_help_flag(self, args):
            return 0

        # Parse format string (simplified)
        format_str = args[0] if args else "%c %m %n %d"

        try:
            # Collect system statistics
            stats = self._collect_stats(client)

            # Format output based on format string
            output = self._format_output(format_str, stats)
            self.console.print(output)

            return 0

        except Exception as e:
            self.console.print(f"[red]nmeter: {e}[/red]")
            return 1

    def _collect_stats(self, client: ClientType) -> dict:
        """Collect system statistics."""
        stats = {"cpu": "0%", "memory": "0%", "network": "0KB/s", "disk": "0KB/s"}

        try:
            # Get memory info
            meminfo = read_proc_file(client, "/proc/meminfo")
            mem_total = 0
            mem_available = 0

            for line in meminfo.split("\n"):
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])

            if mem_total > 0:
                mem_used_pct = int((mem_total - mem_available) * 100 / mem_total)
                stats["memory"] = f"{mem_used_pct}%"
        except (ValueError, IndexError, ZeroDivisionError):
            pass

        try:
            # Get load average for CPU approximation
            loadavg = read_proc_file(client, "/proc/loadavg")
            if loadavg:
                load1 = float(loadavg.split()[0])
                cpu_pct = min(int(load1 * 100), 100)
                stats["cpu"] = f"{cpu_pct}%"
        except (ValueError, IndexError):
            pass

        try:
            # Get network stats (simplified)
            net_dev = read_proc_file(client, "/proc/net/dev")
            total_bytes = 0
            for line in net_dev.split("\n")[2:]:
                if ":" in line:
                    fields = line.split()
                    if len(fields) >= 10:
                        rx_bytes = int(fields[1])
                        tx_bytes = int(fields[9])
                        total_bytes += rx_bytes + tx_bytes

            # Convert to KB/s (approximation)
            kb_per_sec = total_bytes // 1024 // 60  # Rough estimate
            stats["network"] = f"{kb_per_sec}KB/s"
        except (ValueError, IndexError, ZeroDivisionError):
            pass

        return stats

    def _format_output(self, format_str: str, stats: dict) -> str:
        """Format output based on format string."""
        output = format_str
        output = output.replace("%c", stats["cpu"])
        output = output.replace("%m", stats["memory"])
        output = output.replace("%n", stats["network"])
        output = output.replace("%d", stats["disk"])

        # Remove any remaining % characters that weren't recognised
        output = re.sub(r"%[a-zA-Z]", "?", output)

        return output
