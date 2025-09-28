"""Implementation of DumpleasesCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DumpleasesCommand(Command):
    """Implementation of dumpleases command."""

    name = "dumpleases"
    help = "Display DHCP lease information"
    category = "System Information"

    def __init__(self, shell: PebbleShell) -> None:
        super().__init__(shell)

    def show_help(self):
        """Show command help."""
        help_text = """Display DHCP lease information.

Usage: dumpleases [-f leasefile] [-r]

Description:
    Display DHCP lease information from lease files.

Options:
    -f FILE         Specify lease file (default: /var/lib/dhcp/dhcpd.leases)
    -r              Show remaining lease time
    -h, --help      Show this help message

Examples:
    dumpleases              # Display all leases
    dumpleases -f /var/lib/dhcp/dhcpd.leases
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the dumpleases command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "f": str,  # lease file
                "r": bool,  # remaining time
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        lease_file = flags.get("f", "/var/lib/dhcp/dhcpd.leases")
        show_remaining = flags.get("r", False)

        try:
            # Try to read DHCP lease file
            lease_content = ""
            lease_files = [
                lease_file,
                "/var/lib/dhcp/dhcpd.leases",
                "/var/lib/dhcpcd5/dhcpcd.leases",
                "/var/lib/NetworkManager/dhclient.leases",
                "/var/db/dhcpcd.leases",
            ]

            for lfile in lease_files:
                try:
                    with client.pull(lfile, encoding="utf-8") as f:
                        lease_content = f.read()
                        break
                except ops.pebble.PathError:
                    continue

            if not lease_content:
                self.console.print(
                    get_theme().warning_text("No DHCP lease files found")
                )
                return 1

            # Parse lease file (basic parsing)
            leases = []
            current_lease = {}

            for line in lease_content.splitlines():
                line = line.strip()
                if line.startswith("lease ") and line.endswith(" {"):
                    ip = line.split()[1]
                    current_lease = {"ip": ip}
                elif line.startswith("binding state "):
                    current_lease["state"] = line.split(None, 2)[2].rstrip(";")
                elif line.startswith("client-hostname "):
                    hostname = line.split(None, 1)[1].strip('";')
                    current_lease["hostname"] = hostname
                elif line.startswith("hardware ethernet "):
                    mac = line.split(None, 2)[2].rstrip(";")
                    current_lease["mac"] = mac
                elif line.startswith("starts "):
                    starts = line.split(None, 1)[1].rstrip(";")
                    current_lease["starts"] = starts
                elif line.startswith("ends "):
                    ends = line.split(None, 1)[1].rstrip(";")
                    current_lease["ends"] = ends
                elif line == "}":
                    if current_lease and "ip" in current_lease:
                        leases.append(current_lease)
                    current_lease = {}

            # Display leases
            if not leases:
                self.console.print(get_theme().warning_text("No active leases found"))
                return 0

            self.console.print(get_theme().highlight_text("DHCP Leases:"))
            for lease in leases:
                ip = lease.get("ip", "unknown")
                mac = lease.get("mac", "unknown")
                hostname = lease.get("hostname", "")
                state = lease.get("state", "unknown")

                lease_info = f"IP: {ip}, MAC: {mac}"
                if hostname:
                    lease_info += f", Hostname: {hostname}"
                lease_info += f", State: {state}"

                if show_remaining and "ends" in lease:
                    lease_info += f", Ends: {lease['ends']}"

                self.console.print(f"  {lease_info}")

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"dumpleases: {e}"))
            return 1
