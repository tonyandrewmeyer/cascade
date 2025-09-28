"""Implementation of CpuinfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, parse_proc_cpuinfo
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer
    from rich.table import Table


class CpuinfoCommand(Command):
    """Show detailed CPU information."""

    name = "cpuinfo"
    help = "Show CPU information. Use -c for compact format, -t for topology, -a for all CPUs"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute cpuinfo command."""
        if handle_help_flag(self, args):
            return 0
        compact = False
        topology = False
        all_cpus = False

        for arg in args:
            if arg == "-c":
                compact = True
            elif arg == "-t":
                topology = True
            elif arg == "-a":
                all_cpus = True

        try:
            cpuinfo_data = parse_proc_cpuinfo(client)
        except ProcReadError as e:
            self.console.print(f"Error reading CPU information: {e}")
            return 1

        if compact:
            self._display_compact_cpuinfo(cpuinfo_data)
        elif topology:
            self._display_topology_cpuinfo(cpuinfo_data)
        else:
            self._display_full_cpuinfo(cpuinfo_data, all_cpus)

        return 0

    def _display_compact_cpuinfo(
        self, cpuinfo_data: dict[str, int | list[dict[str, str]]]
    ):
        """Display compact CPU information."""
        table = create_enhanced_table()
        table.add_column("CPU", style="cyan", no_wrap=True)
        table.add_column("Model", style="green", no_wrap=False)
        table.add_column("Cores", style="yellow", no_wrap=True)
        table.add_column("Cache", style="blue", no_wrap=True)

        cpus = cpuinfo_data["cpus"]
        assert isinstance(cpus, list), f"cpus should be list, got {type(cpus)}"
        for cpu_num, cpu_info in enumerate(cpus):
            self._add_cpu_row(table, cpu_info, cpu_num)

        self.console.print(table.build())

    def _add_cpu_row(self, table: Table, cpu_info: dict[str, str], cpu_num: int):
        """Add a CPU row to the table."""
        model = cpu_info.get("model name", "Unknown")
        cores = cpu_info.get("cpu cores", "1")
        cache = cpu_info.get("cache size", "Unknown")

        table.add_row(f"CPU {cpu_num}", model, cores, cache)

    def _display_topology_cpuinfo(
        self, cpuinfo_data: dict[str, int | list[dict[str, str]]]
    ):
        """Display CPU topology information."""
        table = create_enhanced_table()
        table.add_column("CPU", style="cyan", no_wrap=True)
        table.add_column("Physical ID", style="green", no_wrap=True)
        table.add_column("Core ID", style="yellow", no_wrap=True)
        table.add_column("Siblings", style="blue", no_wrap=True)
        table.add_column("Core siblings", style="magenta", no_wrap=True)

        cpus = cpuinfo_data["cpus"]
        assert isinstance(cpus, list), f"cpus should be list, got {type(cpus)}"
        for cpu_num, cpu_info in enumerate(cpus):
            self._add_topology_row(table, cpu_info, cpu_num)

        self.console.print(table.build())

    def _add_topology_row(self, table: Table, cpu_info: dict[str, str], cpu_num: int):
        """Add a topology row to the table."""
        physical_id = cpu_info.get("physical id", "0")
        core_id = cpu_info.get("core id", "0")
        siblings = cpu_info.get("siblings", "1")
        core_siblings = cpu_info.get("core siblings", "1")

        table.add_row(f"CPU {cpu_num}", physical_id, core_id, siblings, core_siblings)

    def _display_full_cpuinfo(
        self, cpuinfo_data: dict[str, int | list[dict[str, str]]], all_cpus: bool
    ):
        """Display full CPU information."""
        cpus = cpuinfo_data["cpus"]
        assert isinstance(cpus, list), f"cpus should be list, got {type(cpus)}"

        if all_cpus:
            # Show all CPUs
            content_lines = []
            for cpu_info in cpus:
                for key, value in cpu_info.items():
                    content_lines.append(f"{key}:\t{value}")
                content_lines.append("")  # Empty line between CPUs

            content = "\n".join(content_lines)
            self.console.print(
                Panel(content, title="CPU Information", border_style="bright_blue")
            )
            return

        # Show just the first CPU
        if cpus:
            first_cpu = cpus[0]
            content_lines = []
            for key, value in first_cpu.items():
                content_lines.append(f"{key}:\t{value}")

            content = "\n".join(content_lines)
            self.console.print(
                Panel(
                    content,
                    title="CPU Information",
                    border_style="bright_blue",
                )
            )
