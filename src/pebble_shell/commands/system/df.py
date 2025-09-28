"""Implementation of DiskUsageCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, read_proc_file
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class DiskUsageCommand(Command):
    """Show disk usage information."""

    name = "df"
    help = "Show filesystem disk space usage"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute df command with rich table output."""
        if handle_help_flag(self, args):
            return 0
        try:
            content = read_proc_file(client, "/proc/mounts")
        except ProcReadError as e:
            self.console.print(f"df: failed to read /proc/mounts: {e}")
            return 1

        table = create_enhanced_table()
        table.add_column("Device", style="cyan", no_wrap=True)
        table.add_column("Mount Point", style="green", no_wrap=True)
        table.add_column("Type", style="yellow", no_wrap=True)

        for line in content.splitlines():
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            device = parts[0][:20]
            mount_point = parts[1]
            fs_type = parts[2][:10]
            table.add_row(
                f"[cyan]{device}[/cyan]",
                f"[green]{mount_point}[/green]",
                f"[yellow]{fs_type}[/yellow]",
            )
        self.console.print(table.build())
        return 0
