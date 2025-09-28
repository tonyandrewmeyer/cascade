"""Implementation of iproute command (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class IprouteCommand(Command):
    """Implementation of iproute command (read-only)."""

    name = "iproute"
    help = "Display IP routing table"
    category = "Network"

    def show_help(self):
        """Show command help."""
        help_text = """Display IP routing table.

Usage: iproute [OPTIONS]

Description:
    Display the kernel routing table. Read-only version.
    Simplified version of 'ip route show'.

Options:
    -h, --help      Show this help message

Examples:
    iproute         # Show routing table
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the iproute command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Read routing information from /proc/net/route
            try:
                route_info = read_proc_file(client, "/proc/net/route")
            except ProcReadError:
                self.console.print(
                    "[red]iproute: cannot read routing information[/red]"
                )
                return 1

            lines = route_info.strip().split("\n")

            if len(lines) < 2:
                self.console.print("No routes found")
                return 0

            # Skip header
            for line in lines[1:]:
                fields = line.split()
                if len(fields) >= 8:
                    iface = fields[0]
                    dest = fields[1]
                    gateway = fields[2]
                    metric = fields[6]
                    mask = fields[7]

                    # Convert hex IP addresses to dotted decimal
                    dest_ip = self._hex_to_ip(dest)
                    gw_ip = self._hex_to_ip(gateway)
                    mask_ip = self._hex_to_ip(mask)

                    # Calculate CIDR prefix
                    cidr = self._mask_to_cidr(mask_ip)

                    if dest_ip == "0.0.0.0" and mask_ip == "0.0.0.0":  # noqa: S104 # legitimate use of 0.0.0.0 for default route
                        self.console.print(
                            f"default via {gw_ip} dev {iface} metric {metric}"
                        )
                    else:
                        if cidr == 32:
                            self.console.print(
                                f"{dest_ip} dev {iface} scope link metric {metric}"
                            )
                        else:
                            self.console.print(
                                f"{dest_ip}/{cidr} dev {iface} scope link metric {metric}"
                            )

            return 0

        except Exception as e:
            self.console.print(f"[red]iproute: {e}[/red]")
            return 1

    def _hex_to_ip(self, hex_str: str) -> str:
        """Convert hex string to IP address."""
        if len(hex_str) != 8:
            return "0.0.0.0"  # noqa: S104 # legitimate use of 0.0.0.0 as fallback IP

        try:
            # Reverse byte order for little endian
            ip_int = int(hex_str, 16)
            return f"{ip_int & 0xFF}.{(ip_int >> 8) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 24) & 0xFF}"
        except ValueError:
            return "0.0.0.0"  # noqa: S104 # legitimate use of 0.0.0.0 as fallback IP

    def _mask_to_cidr(self, mask_ip: str) -> int:
        """Convert subnet mask to CIDR prefix length."""
        try:
            parts = mask_ip.split(".")
            if len(parts) != 4:
                return 0

            mask_int = (
                (int(parts[0]) << 24)
                + (int(parts[1]) << 16)
                + (int(parts[2]) << 8)
                + int(parts[3])
            )
            return bin(mask_int).count("1")
        except Exception:
            # Broad exception needed for network address conversion
            return 0
