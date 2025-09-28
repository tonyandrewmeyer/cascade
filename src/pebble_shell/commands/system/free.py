"""Implementation of FreeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils import format_bytes
from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, parse_proc_meminfo
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class FreeCommand(Command):
    """Show memory usage information."""

    name = "free"
    help = "Display memory usage"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute free command with rich table output."""
        if handle_help_flag(self, args):
            return 0

        try:
            memory_info = parse_proc_meminfo(client)
            self._display_memory_info(memory_info, args)
            return 0
        except ProcReadError as e:
            self.console.print(f"Error reading memory information: {e}")
            return 1

    def _display_memory_info(
        self, memory_info: dict[str, int], args: list[str]
    ) -> None:
        """Display memory information in a rich table."""
        human_readable = "-h" in args or "--human" in args
        total = memory_info.get("MemTotal", 0)
        free = memory_info.get("MemFree", 0)
        available = memory_info.get("MemAvailable", free)
        buffers = memory_info.get("Buffers", 0)
        cached = memory_info.get("Cached", 0)
        used = total - free
        swap_total = memory_info.get("SwapTotal", 0)
        swap_free = memory_info.get("SwapFree", 0)
        swap_used = swap_total - swap_free
        table = create_enhanced_table()
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Total", style="green", justify="right")
        table.add_column("Used", style="yellow", justify="right")
        table.add_column("Free", style="blue", justify="right")
        table.add_column("Buff/Cache", style="magenta", justify="right")
        table.add_column("Available", style="white", justify="right")
        if human_readable:
            total_h = format_bytes(total * 1024)
            used_h = format_bytes(used * 1024)
            free_h = format_bytes(free * 1024)
            bufcache_h = format_bytes((buffers + cached) * 1024)
            available_h = format_bytes(available * 1024)
            table.add_row("Mem", total_h, used_h, free_h, bufcache_h, available_h)
            if swap_total > 0:
                swap_total_h = format_bytes(swap_total * 1024)
                swap_used_h = format_bytes(swap_used * 1024)
                swap_free_h = format_bytes(swap_free * 1024)
                table.add_row("Swap", swap_total_h, swap_used_h, swap_free_h, "-", "-")
        else:
            table.add_row(
                "Mem",
                str(total),
                str(used),
                str(free),
                str(buffers + cached),
                str(available),
            )
            if swap_total > 0:
                table.add_row(
                    "Swap", str(swap_total), str(swap_used), str(swap_free), "-", "-"
                )
        self.console.print(table.build())
