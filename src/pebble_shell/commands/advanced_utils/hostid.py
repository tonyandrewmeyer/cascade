"""Implementation of HostidCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union
import socket
import struct

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
    category = "System Utilities"

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

        except OSError as e:
            self.console.print(f"[red]hostid: cannot retrieve host identifier: {e}[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]hostid: unexpected error: {e}[/red]")
            return 1
    
    def _hostname_to_hostid(self, hostname: str) -> str:
        """Convert hostname to hostid using IPv4 address like gethostid()."""
        try:
            # Try to resolve hostname to IPv4 address
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
            if addr_info:
                ipv4_addr = addr_info[0][4][0]
                # Convert IPv4 address to 32-bit integer
                ip_int = struct.unpack("!I", socket.inet_aton(ipv4_addr))[0]
                return f"{ip_int:08x}"
        except (socket.gaierror, socket.error, OSError):
            pass
        
        # Fallback: use hash of hostname (similar to original but more consistent)
        hostname_hash = abs(hash(hostname)) & 0xFFFFFFFF
        return f"{hostname_hash:08x}"
