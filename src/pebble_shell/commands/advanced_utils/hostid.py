"""Implementation of HostidCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file
from ...utils.proc_reader import (
    ProcReadError,
    get_hostname_from_proc_sys,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class HostidCommand(Command):
    """Implementation of hostid command."""

    name = "hostid"
    help = "Display the numeric identifier of the host"
    category = "Advanced Utilities"

    def __init__(self, shell: PebbleShell) -> None:
        super().__init__(shell)

    def show_help(self):
        """Show command help."""
        help_text = """Display the numeric identifier of the host.

Usage: hostid

Description:
    Print the numeric identifier of the current host in hexadecimal.
    This is typically derived from the machine's hardware or system configuration.

Options:
    -h, --help      Show this help message

Examples:
    hostid          # Display host ID
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the hostid command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Try to read hostid from various sources
            hostid = None

            # First try /etc/hostid
            try:
                content = safe_read_file(client, "/etc/hostid")
                if content:
                    content = content.strip()
                    if content:
                        hostid = content
            except ops.pebble.PathError:
                pass

            # If not found, try to derive from machine-id or hostname
            if not hostid:
                try:
                    machine_id_content = safe_read_file(client, "/etc/machine-id")
                    if machine_id_content:
                        machine_id = machine_id_content.strip()
                        # Use first 8 characters as hex hostid
                        hostid = machine_id[:8]
                except ops.pebble.PathError:
                    pass

            # If still not found, try hostname hash
            if not hostid:
                try:
                    hostname = get_hostname_from_proc_sys(client)
                    # Simple hash of hostname to create a hostid
                    hostid = f"{abs(hash(hostname)):08x}"
                except ProcReadError:
                    # Default fallback
                    hostid = "007f0001"  # localhost

            self.console.print(hostid)
            return 0

        except Exception as e:
            self.console.print(f"[red]hostid: {e}[/red]")
            return 1
