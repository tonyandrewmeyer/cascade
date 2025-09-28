"""Implementation of FdinfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops
from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class FdinfoCommand(Command):
    """Show file descriptor information for processes."""

    name = "fdinfo"
    help = "Show file descriptor information. Use -a for all processes, -t for specific types (file, socket, pipe)"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute fdinfo command."""
        if handle_help_flag(self, args):
            return 0
        target_pid = None
        all_processes = False
        fd_type = None

        for arg in args:
            if arg == "-a":
                all_processes = True
            elif arg == "-t":
                fd_type = (
                    args[args.index(arg) + 1]
                    if args.index(arg) + 1 < len(args)
                    else None
                )
            elif not arg.startswith("-") and not target_pid:
                target_pid = arg

        if all_processes:
            self._display_all_processes_fdinfo(client)
        elif target_pid:
            self._display_process_fdinfo(client, target_pid, fd_type)
        else:
            self._display_process_fdinfo(client, "self", fd_type)

        return 0

    def _display_all_processes_fdinfo(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient
    ):
        """Display file descriptor information for all processes."""
        table = create_enhanced_table()
        table.add_column("PID", style="cyan", no_wrap=True)
        table.add_column("Process", style="green", no_wrap=False)
        table.add_column("FD Count", style="yellow", justify="right")
        table.add_column("Types", style="blue", no_wrap=False)

        proc_entries = client.list_files("/proc")
        pids = [entry.name for entry in proc_entries if entry.name.isdigit()]

        for pid in sorted(pids, key=int):
            fd_count, fd_types = self._get_process_fd_summary(client, pid)
            if fd_count > 0:
                process_name = self._get_process_name(client, pid)
                table.add_row(pid, process_name, str(fd_count), ", ".join(fd_types))

        self.console.print(table.build())

    def _display_process_fdinfo(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        pid: str,
        fd_type: str | None,
    ):
        """Display file descriptor information for a specific process."""
        table = create_enhanced_table()
        table.add_column("FD", style="cyan", no_wrap=True)
        table.add_column("Type", style="green", no_wrap=True)
        table.add_column("Flags", style="yellow", no_wrap=True)

        try:
            fd_entries = client.list_files(f"/proc/{pid}/fd")
        except (ops.pebble.PathError, ops.pebble.APIError):
            self.console.print("No file descriptors found.")
            return
        for fd_entry in fd_entries:
            fd = fd_entry.name
            try:
                with client.pull(f"/proc/{pid}/fdinfo/{fd}") as file:
                    fdinfo_content = file.read()
                assert isinstance(fdinfo_content, str)
            except ops.pebble.PathError:
                continue
            fd_type_info = self._parse_fdinfo(fdinfo_content)
            if fd_type and fd_type_info.get("type") != fd_type:
                continue
            table.add_row(
                fd,
                fd_type_info.get("type", "unknown"),
                fd_type_info.get("flags", ""),
            )
        if table.row_count == 0:
            self.console.print("No file descriptors found.")
            return
        process_name = self._get_process_name(client, pid)
        self.console.print(
            Panel(
                table,
                title=f"File Descriptors - PID {pid} ({process_name})",
                border_style="bright_blue",
            )
        )

    def _get_process_fd_summary(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> tuple[int, list[str]]:
        """Get file descriptor summary for a process."""
        fd_count = 0
        fd_types: set[str] = set()

        try:
            fd_entries = client.list_files(f"/proc/{pid}/fd")
        except (ops.pebble.PathError, ops.pebble.APIError):
            return 0, []
        fd_count = len(fd_entries)

        for fd_entry in fd_entries:
            fd = fd_entry.name
            try:
                with client.pull(f"/proc/{pid}/fdinfo/{fd}") as file:
                    fdinfo_content = file.read()
                assert isinstance(fdinfo_content, str)
            except ops.pebble.PathError:
                continue
            fd_type_info = self._parse_fdinfo(fdinfo_content)
            fd_types.add(fd_type_info.get("type", "unknown"))

        return fd_count, list(fd_types)

    def _get_process_name(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> str:
        """Get process name."""
        try:
            with client.pull(f"/proc/{pid}/comm") as file:
                content = file.read()
            assert isinstance(content, str)
        except ops.pebble.PathError:
            return "unknown"
        return content.strip()

    def _parse_fdinfo(self, content: str) -> dict[str, str]:
        """Parse fdinfo content."""
        info: dict[str, str] = {}

        for line in content.splitlines():
            if line.startswith("pos:"):
                info["position"] = line.split(":")[1].strip()
            elif line.startswith("flags:"):
                flags = line.split(":")[1].strip()
                info["flags"] = flags
                if "O_RDONLY" in flags or "O_WRONLY" in flags or "O_RDWR" in flags:
                    info["type"] = "file"
                else:
                    info["type"] = "unknown"
            elif line.startswith("mnt_id:"):
                info["mnt_id"] = line.split(":")[1].strip()
            elif line.startswith("ino:"):
                info["ino"] = line.split(":")[1].strip()

        return info
