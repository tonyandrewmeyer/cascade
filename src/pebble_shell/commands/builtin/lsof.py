"""Implementation of LsofCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops
from rich.panel import Panel
from rich.table import Table

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LsofCommand(Command):
    """Command for listing open files."""
    name = "lsof"
    help = "List open files. Usage: lsof"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the lsof command to list open files."""
        if handle_help_flag(self, args):
            return 0
        console = self.console
        table = Table(
            show_header=True, header_style="bold magenta", box=None, expand=False
        )
        table.add_column("PID", style="cyan", no_wrap=True)
        table.add_column("USER", style="white", no_wrap=True)
        table.add_column("FD", style="white", no_wrap=True)
        table.add_column("TYPE", style="white", no_wrap=True)
        table.add_column("DEVICE", style="white", no_wrap=True)
        table.add_column("SIZE/OFF", style="white", no_wrap=True)
        table.add_column("NODE", style="white", no_wrap=True)
        table.add_column("NAME", style="green")
        proc_entries = client.list_files("/proc")
        for entry in proc_entries:
            if not entry.name.isdigit():
                continue
            pid = entry.name
            user = "?"
            with client.pull(f"/proc/{pid}/status") as f:
                status_content = f.read()
                assert isinstance(status_content, str)
                for line in status_content.splitlines():
                    if line.startswith("Uid:"):
                        uid = int(line.split()[1])
                        try:
                            user = pwd.getpwuid(uid).pw_name
                        except Exception:
                            user = str(uid)
                        break
            fd_entries = client.list_files(f"/proc/{pid}/fd")
            for fd_entry in fd_entries:
                fd = fd_entry.name
                name = fd_entry.name
                if fd_entry.type == ops.pebble.FileType.FILE:
                    ftype = "REG"
                elif fd_entry.type == ops.pebble.FileType.DIRECTORY:
                    ftype = "DIR"
                elif fd_entry.type == ops.pebble.FileType.SYMLINK:
                    ftype = "LNK"
                else:
                    ftype = "?"
                device = "?"
                size_off = "?"
                node = "?"
                # Try to get fdinfo for size/off.
                with client.pull(f"/proc/{pid}/fdinfo/{fd}") as f:
                    fdinfo_content = f.read()
                    assert isinstance(fdinfo_content, str)
                    for line in fdinfo_content.splitlines():
                        if line.startswith("pos:"):
                            size_off = line.split()[1]
                table.add_row(pid, user, fd, ftype, device, size_off, node, name)
        if table.row_count == 0:
            console.print(
                Panel("No open files found.", title="[b]lsof[/b]", style="cyan")
            )
            return 1
        console.print(table)
        return 0
