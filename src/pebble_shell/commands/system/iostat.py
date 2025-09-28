"""Implementation of IostatCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rich import box
from rich.table import Table

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, parse_proc_diskstats, parse_proc_stat
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class IostatCommand(Command):
    """Display I/O statistics."""

    name = "iostat"
    help = "Display I/O statistics. Optional: interval (seconds) and count (number of reports)"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute iostat command."""
        if handle_help_flag(self, args):
            return 0
        interval = 1
        count = 1

        # Parse arguments
        if len(args) >= 1:
            try:
                interval = float(args[0])
                if interval < 0.1:
                    self.console.print("Error: interval must be at least 0.1 seconds")
                    return 1
            except ValueError:
                self.console.print("Error: interval must be a number")
                return 1

        if len(args) >= 2:
            try:
                count = int(args[1])
                if count < 1:
                    self.console.print("Error: count must be at least 1")
                    return 1
            except ValueError:
                self.console.print("Error: count must be a number")
                return 1

        # Run iostat for specified count
        for i in range(count):
            if i > 0:
                time.sleep(interval)

            stats = self._get_iostat_data(client)
            if stats is None:
                return 1

            self._display_iostat(stats, i == 0)  # Show header only for first iteration

        return 0

    def _get_iostat_data(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient
    ) -> dict[str, Any] | None:
        """Get iostat data from /proc filesystem."""
        try:
            # Get disk stats from /proc/diskstats
            disk_stats = parse_proc_diskstats(client)

            # Get CPU stats from /proc/stat for I/O wait
            stat_data = parse_proc_stat(client)
            cpu_io_wait = stat_data["cpu"].get("iowait", 0)

            return {"disks": disk_stats, "cpu_io_wait": cpu_io_wait}

        except ProcReadError as e:
            self.console.print(f"[red]Error reading iostat data: {e}[/red]")
            return None

    def _display_iostat(self, stats: dict[str, Any], show_header: bool = True):
        """Display iostat output."""
        disks = stats["disks"]
        cpu_io_wait = stats["cpu_io_wait"]

        # Create table
        table = Table(
            show_header=show_header,
            header_style="bold magenta",
            box=box.SIMPLE_HEAVY,
            expand=False,
            border_style="bright_blue",
        )

        if show_header:
            table.add_column("Device", style="cyan", no_wrap=True)
            table.add_column("Reads/s", style="yellow", no_wrap=True)
            table.add_column("Writes/s", style="yellow", no_wrap=True)
            table.add_column("Read KB/s", style="green", no_wrap=True)
            table.add_column("Write KB/s", style="green", no_wrap=True)
            table.add_column("IO Wait %", style="red", no_wrap=True)
            table.add_column("Util %", style="red", no_wrap=True)

        # Calculate and display disk statistics
        for disk in disks:
            device = disk["device"]
            reads = disk["reads"]
            read_sectors = disk["read_sectors"]
            write_sectors = disk["write_sectors"]
            io_time = disk["io_time"]

            # Convert sectors to KB (1 sector = 512 bytes = 0.5 KB)
            read_kb = read_sectors * 0.5
            write_kb = write_sectors * 0.5

            # Calculate utilization percentage
            util_pct = (io_time / 1000.0) * 100 if io_time > 0 else 0

            # For now, we'll show static values since we need historical data for rates
            reads_per_sec = "N/A"  # Would need historical data
            writes_per_sec = "N/A"  # Would need historical data
            read_kb_per_sec = "N/A"  # Would need historical data
            write_kb_per_sec = "N/A"  # Would need historical data

            table.add_row(
                device,
                str(reads_per_sec),
                str(writes_per_sec),
                str(read_kb_per_sec),
                str(write_kb_per_sec),
                f"{cpu_io_wait:.1f}",
                f"{util_pct:.1f}",
            )

        # Display the table
        if show_header:
            self.console.print("I/O Statistics:")
        self.console.print(table)

        # Show summary statistics
        if disks:
            total_reads = sum(d["reads"] for d in disks)
            total_writes = sum(d["writes"] for d in disks)
            total_read_sectors = sum(d["read_sectors"] for d in disks)
            total_write_sectors = sum(d["write_sectors"] for d in disks)

            self.console.print("\nSummary:")
            self.console.print(f"  Total reads: {total_reads}")
            self.console.print(f"  Total writes: {total_writes}")
            self.console.print(f"  Total read sectors: {total_read_sectors}")
            self.console.print(f"  Total write sectors: {total_write_sectors}")
            self.console.print(f"  CPU I/O wait: {cpu_io_wait}")

        # Also show traditional iostat format
        self.console.print("\nTraditional iostat format:")
        self.console.print(
            "Device            tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn"
        )
        for disk in disks:
            device = disk["device"]
            reads = disk["reads"]
            writes = disk["writes"]
            read_sectors = disk["read_sectors"]
            write_sectors = disk["write_sectors"]

            read_kb = read_sectors * 0.5
            write_kb = write_sectors * 0.5

            # Total operations per second (simplified)
            total_ops = reads + writes

            self.console.print(
                f"{device:16s} {total_ops:4d} {read_kb:12.1f} {write_kb:12.1f} {read_kb:10.0f} {write_kb:10.0f}"
            )
