"""Implementation of VmstatCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rich import box
from rich.table import Table

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    parse_proc_meminfo,
    parse_proc_stat,
    parse_proc_vmstat,
)
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class VmstatCommand(Command):
    """Display virtual memory statistics."""

    name = "vmstat"
    help = "Display virtual memory statistics. Optional: interval (seconds) and count (number of reports)"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute vmstat command."""
        if handle_help_flag(self, args):
            return 0
        interval = 1
        count = 1

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

        # Run vmstat for specified count.
        for i in range(count):
            if i > 0:
                time.sleep(interval)

            stats = self._get_vmstat_data(client)
            if stats is None:
                return 1

            self._display_vmstat(stats, i == 0)  # Show header only for first iteration

        return 0

    def _get_vmstat_data(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient
    ) -> dict[str, Any] | None:
        """Get vmstat data from /proc filesystem."""
        try:
            # Get CPU stats from /proc/stat
            stat_data = parse_proc_stat(client)
            cpu_stats = stat_data["cpu"]

            # Get memory stats from /proc/meminfo
            mem_stats = parse_proc_meminfo(client)

            # Get vmstat data from /proc/vmstat (optional)
            try:
                vm_stats = parse_proc_vmstat(client)
            except ProcReadError:
                vm_stats = {}

            return {"cpu": cpu_stats, "memory": mem_stats, "vmstat": vm_stats}

        except ProcReadError as e:
            self.console.print(f"[red]Error reading vmstat data: {e}[/red]")
            return None

    def _display_vmstat(self, stats: dict[str, Any], show_header: bool = True):
        """Display vmstat output."""
        cpu = stats["cpu"]
        mem = stats["memory"]
        vm = stats["vmstat"]

        # Calculate CPU percentages
        total_cpu = sum(cpu.values())
        if total_cpu > 0:
            cpu_user = (cpu["user"] / total_cpu) * 100
            cpu_system = (cpu["system"] / total_cpu) * 100
            cpu_idle = (cpu["idle"] / total_cpu) * 100
            cpu_iowait = (cpu["iowait"] / total_cpu) * 100
        else:
            cpu_user = cpu_system = cpu_idle = cpu_iowait = 0

        # Memory calculations (in KB)
        mem_total = mem.get("MemTotal", 0)
        mem_free = mem.get("MemFree", 0)
        mem_available = mem.get("MemAvailable", mem_free)
        mem_used = mem_total - mem_available if mem_total > 0 else 0
        mem_buffers = mem.get("Buffers", 0)
        mem_cached = mem.get("Cached", 0)

        # Virtual memory calculations
        swap_total = mem.get("SwapTotal", 0)
        swap_free = mem.get("SwapFree", 0)
        swap_used = swap_total - swap_free if swap_total > 0 else 0

        # VM statistics
        pgpgin = vm.get("pgpgin", 0)
        pgpgout = vm.get("pgpgout", 0)
        pswpin = vm.get("pswpin", 0)
        pswpout = vm.get("pswpout", 0)

        # Create table
        table = Table(
            show_header=show_header,
            header_style="bold magenta",
            box=box.SIMPLE_HEAVY,
            expand=False,
            border_style="bright_blue",
        )

        if show_header:
            table.add_column("Category", style="cyan", no_wrap=True)
            table.add_column("Value", style="yellow", no_wrap=True)
            table.add_column("Details", style="green", no_wrap=False)

        # CPU section
        table.add_row(
            "CPU Usage",
            f"{cpu_user:.1f}% user, {cpu_system:.1f}% system",
            f"idle: {cpu_idle:.1f}%, iowait: {cpu_iowait:.1f}%",
        )

        # Memory section
        mem_usage_pct = (mem_used / mem_total * 100) if mem_total > 0 else 0
        table.add_row(
            "Memory",
            f"{mem_used // 1024}M used / {mem_total // 1024}M total",
            f"{mem_usage_pct:.1f}% used, {mem_available // 1024}M available",
        )

        # Swap section
        if swap_total > 0:
            swap_usage_pct = swap_used / swap_total * 100
            table.add_row(
                "Swap",
                f"{swap_used // 1024}M used / {swap_total // 1024}M total",
                f"{swap_usage_pct:.1f}% used",
            )

        # Buffer/Cache section
        table.add_row(
            "Buffers/Cache",
            f"{mem_buffers // 1024}M buffers, {mem_cached // 1024}M cached",
            f"Total: {(mem_buffers + mem_cached) // 1024}M",
        )

        # VM activity
        table.add_row(
            "VM Activity",
            f"pgpgin: {pgpgin // 1024}K, pgpgout: {pgpgout // 1024}K",
            f"pswpin: {pswpin}, pswpout: {pswpout}",
        )

        # Display the table
        if show_header:
            self.console.print("Virtual Memory Statistics:")
        self.console.print(table)

        # Also show traditional vmstat format
        self.console.print("\nTraditional vmstat format:")
        self.console.print(
            "procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----"
        )
        self.console.print(
            " r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st"
        )
        self.console.print(
            f" 0  0 {swap_used // 1024:6d} {mem_free // 1024:6d} {mem_buffers // 1024:6d} {mem_cached // 1024:6d} {pswpin:4d} {pswpout:4d} {pgpgin // 1024:4d} {pgpgout // 1024:4d} {0:4d} {0:4d} {cpu_user:2.0f} {cpu_system:2.0f} {cpu_idle:2.0f} {cpu_iowait:2.0f} {0:2d}"
        )
