"""Implementation of MeminfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, parse_proc_meminfo
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class MeminfoCommand(Command):
    """Show detailed memory information."""

    name = "meminfo"
    help = "Show memory information. Use -d for detailed breakdown, -s for summary"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute meminfo command."""
        if handle_help_flag(self, args):
            return 0
        detailed = False
        summary = False

        for arg in args:
            if arg == "-d":
                detailed = True
            elif arg == "-s":
                summary = True

        try:
            meminfo_data = parse_proc_meminfo(client)
        except ProcReadError as e:
            self.console.print(f"Error reading memory information: {e}")
            return 1

        if summary:
            self._display_summary_meminfo(meminfo_data)
        else:
            self._display_meminfo(meminfo_data, detailed)

        return 0

    def _display_summary_meminfo(self, meminfo_data: dict[str, int]):
        """Display summary memory information."""
        table = create_enhanced_table()
        table.add_column("Memory Type", style="cyan", no_wrap=True)
        table.add_column("Total (KB)", style="green", justify="right")
        table.add_column("Used (KB)", style="yellow", justify="right")
        table.add_column("Free (KB)", style="blue", justify="right")
        table.add_column("Usage %", style="red", justify="right")

        # Main memory
        total = meminfo_data.get("MemTotal", 0)
        free = meminfo_data.get("MemFree", 0)
        available = meminfo_data.get("MemAvailable", free)
        used = total - available if total > 0 else 0
        usage_pct = (used / total * 100) if total > 0 else 0

        table.add_row(
            "Main Memory",
            f"{total:,}",
            f"{used:,}",
            f"{available:,}",
            f"{usage_pct:.1f}%",
        )

        # Swap memory
        swap_total = meminfo_data.get("SwapTotal", 0)
        swap_free = meminfo_data.get("SwapFree", 0)
        swap_used = swap_total - swap_free if swap_total > 0 else 0
        swap_usage_pct = (swap_used / swap_total * 100) if swap_total > 0 else 0

        if swap_total > 0:
            table.add_row(
                "Swap",
                f"{swap_total:,}",
                f"{swap_used:,}",
                f"{swap_free:,}",
                f"{swap_usage_pct:.1f}%",
            )

        self.console.print(table.build())

    def _display_meminfo(self, meminfo_data: dict[str, int], detailed: bool):
        """Display memory information."""
        if detailed:
            # Create detailed content from the parsed data
            content_lines = []
            for key, value in meminfo_data.items():
                content_lines.append(f"{key}:\t{value} kB")
            content = "\n".join(content_lines)

            self.console.print(
                Panel(content, title="Memory Information", border_style="bright_blue")
            )
        else:
            table = create_enhanced_table()
            table.add_column("Memory Type", style="cyan", no_wrap=True)
            table.add_column("Value (KB)", style="green", justify="right")
            table.add_column("Description", style="white", no_wrap=False)

            key_stats: list[tuple[str, str]] = [
                ("MemTotal", "Total RAM"),
                ("MemFree", "Free RAM"),
                ("MemAvailable", "Available RAM"),
                ("Buffers", "Kernel buffers"),
                ("Cached", "Page cache"),
                ("SwapCached", "Swap cache"),
                ("Active", "Active memory"),
                ("Inactive", "Inactive memory"),
                ("SwapTotal", "Total swap"),
                ("SwapFree", "Free swap"),
                ("Dirty", "Dirty pages"),
                ("Writeback", "Writeback pages"),
                ("AnonPages", "Anonymous pages"),
                ("Mapped", "Mapped pages"),
                ("Shmem", "Shared memory"),
                ("Slab", "Kernel slab"),
                ("SReclaimable", "Reclaimable slab"),
                ("SUnreclaim", "Unreclaimable slab"),
                ("KernelStack", "Kernel stack"),
                ("PageTables", "Page tables"),
                ("NFS_Unstable", "NFS unstable"),
                ("Bounce", "Bounce buffer"),
                ("WritebackTmp", "Writeback temp"),
                ("CommitLimit", "Commit limit"),
                ("Committed_AS", "Committed memory"),
                ("VmallocTotal", "Total vmalloc"),
                ("VmallocUsed", "Used vmalloc"),
                ("VmallocChunk", "Largest vmalloc chunk"),
                ("HardwareCorrupted", "Hardware corrupted"),
                ("AnonHugePages", "Anonymous huge pages"),
                ("ShmemHugePages", "Shared huge pages"),
                ("ShmemPmdMapped", "Shared PMD mapped"),
                ("CmaTotal", "Total CMA"),
                ("CmaFree", "Free CMA"),
                ("HugePages_Total", "Total huge pages"),
                ("HugePages_Free", "Free huge pages"),
                ("HugePages_Rsvd", "Reserved huge pages"),
                ("HugePages_Surp", "Surplus huge pages"),
                ("Hugepagesize", "Huge page size"),
                ("DirectMap4k", "Direct mapped 4k"),
                ("DirectMap2M", "Direct mapped 2M"),
                ("DirectMap1G", "Direct mapped 1G"),
            ]

            for stat_name, description in key_stats:
                if stat_name in meminfo_data:
                    value = meminfo_data[stat_name]
                    table.add_row(stat_name, f"{value:,}", description)

            self.console.print(table.build())
