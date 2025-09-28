"""Implementation of LoadavgCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    parse_proc_cpuinfo,
    parse_proc_loadavg,
    parse_proc_uptime,
)
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class LoadavgCommand(Command):
    """Display detailed load average information."""

    name = "loadavg"
    help = "Display detailed load average information from /proc/loadavg"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute loadavg command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Get load average information
            loadavg_info = parse_proc_loadavg(client)
            load_1min = float(loadavg_info["load_1min"])
            load_5min = float(loadavg_info["load_5min"])
            load_15min = float(loadavg_info["load_15min"])
            running_processes = loadavg_info["running_processes"]
            total_processes = loadavg_info["total_processes"]
            last_pid = str(loadavg_info["last_pid"])

            # Get CPU core count
            try:
                cpuinfo_data = parse_proc_cpuinfo(client)
                cpu_cores = cpuinfo_data["cpu_count"]
            except ProcReadError:
                cpu_cores = 0

            # Get uptime information
            try:
                uptime_info = parse_proc_uptime(client)
                uptime_seconds = uptime_info["uptime_seconds"]
            except ProcReadError:
                uptime_seconds = 0.0

        except ProcReadError as e:
            self.console.print(f"Error reading load average data: {e}")
            return 1

        self._display_loadavg(
            load_1min,
            load_5min,
            load_15min,
            running_processes,
            total_processes,
            last_pid,
            cpu_cores,
            uptime_seconds,
        )

        return 0

    def _display_loadavg(
        self,
        load_1min: float,
        load_5min: float,
        load_15min: float,
        running_processes: int,
        total_processes: int,
        last_pid: str,
        cpu_cores: int,
        uptime_seconds: float,
    ):
        """Display load average information."""
        # Create table
        table = create_enhanced_table()

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow", no_wrap=True)
        table.add_column("Details", style="green", no_wrap=False)

        # Load averages
        table.add_row(
            "Load Average (1 min)",
            f"{load_1min:.2f}",
            "Average system load over 1 minute",
        )

        table.add_row(
            "Load Average (5 min)",
            f"{load_5min:.2f}",
            "Average system load over 5 minutes",
        )

        table.add_row(
            "Load Average (15 min)",
            f"{load_15min:.2f}",
            "Average system load over 15 minutes",
        )

        # CPU cores
        table.add_row("CPU Cores", str(cpu_cores), "Number of CPU cores available")

        # Load per core
        if cpu_cores > 0:
            load_per_core_1min = load_1min / cpu_cores
            load_per_core_5min = load_5min / cpu_cores
            load_per_core_15min = load_15min / cpu_cores

            table.add_row(
                "Load per Core (1 min)",
                f"{load_per_core_1min:.2f}",
                "Load average per CPU core (1 min)",
            )

            table.add_row(
                "Load per Core (5 min)",
                f"{load_per_core_5min:.2f}",
                "Load average per CPU core (5 min)",
            )

            table.add_row(
                "Load per Core (15 min)",
                f"{load_per_core_15min:.2f}",
                "Load average per CPU core (15 min)",
            )

        # Process information
        table.add_row(
            "Running Processes",
            str(running_processes),
            "Number of processes currently running",
        )

        table.add_row(
            "Total Processes", str(total_processes), "Total number of processes"
        )

        # Uptime
        if uptime_seconds > 0:
            uptime_days = int(uptime_seconds // 86400)
            uptime_hours = int((uptime_seconds % 86400) // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)

            uptime_str = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
            table.add_row("System Uptime", uptime_str, "Time since last system boot")

        # Last PID
        table.add_row(
            "Last PID",
            str(last_pid),
            "Process ID of the most recently created process",
        )

        # Display the table
        self.console.print("Load Average Information:")
        self.console.print(table.build())

        # Show interpretation
        self.console.print("\nInterpretation:")
        if cpu_cores > 0:
            if load_1min > cpu_cores:
                self.console.print(
                    f"  ⚠️  System is under high load (1 min: {load_1min:.2f} > {cpu_cores} cores)"
                )
            elif load_1min > cpu_cores * 0.7:
                self.console.print(
                    f"  ⚡ System is moderately loaded (1 min: {load_1min:.2f} > {cpu_cores * 0.7:.1f})"
                )
            else:
                self.console.print(
                    f"  ✅ System load is normal (1 min: {load_1min:.2f} < {cpu_cores} cores)"
                )

        # Show traditional format
        self.console.print("\nTraditional format:")
        self.console.print(
            f"load average: {load_1min:.2f}, {load_5min:.2f}, {load_15min:.2f}"
        )
        self.console.print(f"processes: {running_processes}/{total_processes}")
        self.console.print(f"last pid: {last_pid}")
