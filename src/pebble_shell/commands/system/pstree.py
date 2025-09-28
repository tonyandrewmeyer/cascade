"""Implementation of PstreeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    read_proc_cmdline,
    read_proc_status_fields,
)
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class PstreeCommand(Command):
    """Show process tree."""

    name = "pstree"
    help = "Show process tree"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute pstree command."""
        if handle_help_flag(self, args):
            return 0
        try:
            # Get all process directories
            proc_entries = client.list_files("/proc")
            pids = [entry.name for entry in proc_entries if entry.name.isdigit()]

            if not pids:
                print("No processes found")
                return 1

            # Build process tree
            process_tree = self._build_process_tree(client, pids)

            # Display tree
            self._display_process_tree(process_tree)

        except Exception as e:
            print(f"Error building process tree: {e}")
            return 1

        return 0

    def _build_process_tree(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pids: list[str]
    ) -> dict[str, dict[str, str]]:
        """Build process tree from PIDs."""
        process_info: dict[str, dict[str, str]] = {}

        for pid in pids:
            try:
                # Use proc_reader utilities for process information
                try:
                    status_fields = read_proc_status_fields(
                        client, pid, ["PPid", "Name"]
                    )
                    ppid = status_fields.get("PPid")
                    name = status_fields.get("Name")
                except ProcReadError:
                    ppid = None
                    name = None

                # Read process command line using proc_reader utility
                cmdline = read_proc_cmdline(client, pid)

                if name and ppid:
                    process_info[pid] = {"name": name, "ppid": ppid, "cmdline": cmdline}

            except Exception:  # noqa: PERF203, S112
                continue

        return process_info

    def _display_process_tree(self, process_tree: dict[str, dict[str, str]]):
        """Display process tree in a tree-like format."""
        # Find root processes (processes with PPID 0 or not in our list)
        roots: list[str] = []

        for pid, info in process_tree.items():
            if info["ppid"] == "0" or info["ppid"] not in process_tree:
                roots.append(pid)

        if not roots:
            # If no clear roots, show all processes
            roots = list(process_tree.keys())

        # Display tree starting from roots
        for root_pid in sorted(roots, key=int):
            self._display_process_branch(process_tree, root_pid, "", set())

    def _display_process_branch(
        self,
        process_tree: dict[str, dict[str, str]],
        pid: str,
        prefix: str,
        visited: set[str],
    ):
        """Display a branch of the process tree."""
        if pid in visited:
            return

        visited.add(pid)
        info = process_tree.get(pid)
        if not info:
            return

        # Display current process
        name = info["name"]
        cmdline = info["cmdline"]

        # Escape any Rich formatting characters in the process name and command line
        name = name.replace("[", "\\[").replace("]", "\\]")
        cmdline = cmdline.replace("[", "\\[").replace("]", "\\]")

        if cmdline != "unknown" and cmdline != name:
            display_name = f"{name}({pid}) [{cmdline[:30]}]"
        else:
            display_name = f"{name}({pid})"

        # Use plain text output to avoid Rich parsing issues
        self.console.print(f"{prefix}{display_name}")

        # Find children
        children = [
            child_pid
            for child_pid, child_info in process_tree.items()
            if child_info["ppid"] == pid
        ]

        # Display children
        for i, child_pid in enumerate(sorted(children, key=int)):
            is_last = i == len(children) - 1
            child_prefix = prefix + ("└── " if is_last else "├── ")
            self._display_process_branch(process_tree, child_pid, child_prefix, visited)
