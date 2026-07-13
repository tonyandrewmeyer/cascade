"""Running command for Cascade.

This module provides implementation for the running command that shows
processes matching a search pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from ...utils.proc_reader import ProcReadError, read_proc_cmdline, read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class RunningCommand(Command):
    """Show running processes, optionally filtered by pattern."""

    name = "running"
    help = "Show running processes matching a pattern"
    category = "System"

    def show_help(self):
        """Show command help."""
        help_text = """Show running processes, optionally filtered by pattern.

Usage: running [OPTIONS] [PATTERN...]

Options:
    -h, --help      Show this help message
    -i, --ignore    Case-insensitive matching (default)
    -c, --case      Case-sensitive matching

Arguments:
    PATTERN         Optional search patterns to filter processes
                    Multiple patterns are matched with OR logic

Without patterns, shows all running processes.
With patterns, shows only processes whose command line matches.

Examples:
    running             # Show all processes
    running python      # Show python processes
    running nginx java  # Show nginx OR java processes
    running -c Python   # Case-sensitive search for Python
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the running command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "i": bool,
                "ignore": bool,
                "c": bool,
                "case": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, patterns = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        # Case sensitivity (default is case-insensitive)
        case_sensitive = flags["c"] or flags["case"]

        # Get list of process directories
        try:
            proc_entries = client.list_files("/proc")
            pids = [entry.name for entry in proc_entries if entry.name.isdigit()]
        except ops.pebble.PathError as e:
            self.console.print(f"[red]running: cannot read /proc: {e}[/red]")
            return 1

        if not pids:
            self.console.print("[yellow]No processes found[/yellow]")
            return 0

        # Collect process info
        processes: list[tuple[str, str]] = []
        for pid in sorted(pids, key=int):
            cmdline = read_proc_cmdline(client, pid)
            if cmdline == "unknown":
                # Try to get comm instead
                try:
                    comm = read_proc_file(client, f"/proc/{pid}/comm")
                    cmdline = f"[{comm.strip()}]"
                except ProcReadError:
                    continue

            processes.append((pid, cmdline))

        # Filter by patterns if provided
        if patterns:
            filtered = []
            for pid, cmdline in processes:
                match_target = cmdline if case_sensitive else cmdline.lower()
                for pattern in patterns:
                    match_pattern = pattern if case_sensitive else pattern.lower()
                    if match_pattern in match_target:
                        filtered.append((pid, cmdline))
                        break
            processes = filtered

        if not processes:
            if patterns:
                self.console.print(
                    f"[yellow]No processes found matching: {' '.join(patterns)}[/yellow]"
                )
            else:
                self.console.print("[yellow]No processes found[/yellow]")
            return 1

        # Display results with highlighted PIDs
        for pid, cmdline in processes:
            self.console.print(f"[magenta]{pid:>7}[/magenta]  {cmdline}")

        return 0
