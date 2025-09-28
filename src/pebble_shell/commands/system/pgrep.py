"""Implementation of PgrepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.error_handling import handle_pebble_path_error
from ...utils.proc_reader import (
    ProcReadError,
    get_user_name_for_uid,
    read_proc_cmdline,
    read_proc_file,
    read_proc_status_field,
)
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class PgrepCommand(Command):
    """Find processes by name or command line pattern."""

    name = "pgrep"
    help = "Find processes by name or command line pattern. Use -f for full command matching, -u for user filtering"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute pgrep command."""
        if handle_help_flag(self, args):
            return 0
        if not args:
            self.console.print("Usage: pgrep [-f] [-u user] [pattern]")
            self.console.print("  -f: Match against full command line")
            self.console.print("  -u: Filter by username")
            return 1

        # Parse options
        full_match = False
        user_filter = None
        pattern = None

        i = 0
        while i < len(args):
            arg = args[i]

            if arg == "-f":
                full_match = True
                i += 1
            elif arg == "-u":
                if i + 1 >= len(args):
                    self.console.print("Error: -u requires a username")
                    return 1
                user_filter = args[i + 1]
                i += 2
            elif arg.startswith("-"):
                self.console.print(f"Error: Unknown option {arg}")
                return 1
            else:
                pattern = arg
                i += 1

        if not pattern and not user_filter:
            self.show_help()
            return 1

        # Get all processes.
        try:
            proc_entries = client.list_files("/proc")
            pids = [entry.name for entry in proc_entries if entry.name.isdigit()]
        except ops.pebble.PathError as e:
            handle_pebble_path_error(self.console, "list processes", "/proc", e)
            return 1

        if not pids:
            self.console.print("No processes found")
            return 1

        matching_pids: list[str] = []
        for pid in pids:
            # Get process name.
            try:
                comm = read_proc_file(client, f"/proc/{pid}/comm").strip()
            except ProcReadError:
                continue

            # Get full command line if needed.
            cmdline = ""
            if full_match:
                cmdline = read_proc_cmdline(client, pid)
                if cmdline == "unknown":
                    cmdline = comm

            # Get user info if filtering by user.
            if user_filter:
                try:
                    uid = read_proc_status_field(client, pid, "Uid")
                    if uid:
                        username = get_user_name_for_uid(client, uid) or f"uid{uid}"
                        if username != user_filter:
                            continue
                    else:
                        continue
                except ProcReadError:
                    continue

            # Check if process matches pattern.
            if pattern:
                search_text = cmdline if full_match else comm
                assert isinstance(search_text, str)
                if pattern.lower() in search_text.lower():
                    matching_pids.append(pid)
            else:
                matching_pids.append(pid)

        # Display results
        if not matching_pids:
            self.console.print(f"No processes found matching '{pattern}'")
            return 1

        # Sort PIDs numerically.
        matching_pids.sort(key=int)

        # Show matching processes in a table
        table = create_enhanced_table()
        table.add_column("PID", style="cyan", no_wrap=True)
        table.add_column("User", style="green", no_wrap=True)
        table.add_column("Command", style="yellow", no_wrap=False)

        for pid in matching_pids:
            # Get user info
            try:
                uid = read_proc_status_field(client, pid, "Uid")
                username = (
                    get_user_name_for_uid(client, uid) or f"uid{uid}"
                    if uid
                    else "unknown"
                )
            except ProcReadError:
                username = "unknown"

            # Get command line
            cmdline = read_proc_cmdline(client, pid)
            if cmdline == "unknown":
                try:
                    comm_content = read_proc_file(client, f"/proc/{pid}/comm")
                    cmdline = f"[{comm_content.strip()}]"
                except ProcReadError:
                    cmdline = "unknown"

            # Truncate command if too long.
            if len(cmdline) > 50:
                cmdline = cmdline[:47] + "..."

            table.add_row(pid, username, cmdline)

        print(f"Found {len(matching_pids)} matching process(es):")
        self.console.print(table.build())

        # Also show just PIDs (like real pgrep)
        pids_only = " ".join(matching_pids)
        print(f"\nPIDs: {pids_only}")

        return 0
