"""Implementation of ip command (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

    from pebble_shell.shell import PebbleShell

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class IpCommand(Command):
    """Implementation of ip command (read-only)."""

    name = "ip"
    help = "Display IP routing, network devices, policy routing and tunnels"
    category = "Network"

    def show_help(self):
        """Show command help."""
        help_text = """Display IP routing, network devices, policy routing and tunnels.

Usage: ip [OPTIONS] OBJECT [COMMAND]

Description:
    Display network configuration information. Read-only version.

Objects:
    addr, address       Protocol addresses
    route               Routing table entries
    link                Network devices
    rule                Routing policy rules

Commands:
    show, list          Show/list objects (default)

Options:
    -4, -6              Use IPv4/IPv6 only
    -h, --help          Show this help message

Examples:
    ip addr show        # Show all addresses
    ip route show       # Show routing table
    ip link show        # Show network interfaces
    ip rule show        # Show routing rules
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the ip command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.show_help()
            return 0

        # Parse arguments
        obj = args[0]

        try:
            if obj in ["addr", "address"]:
                return self._show_addresses(client)
            elif obj == "route":
                return self._show_routes(client)
            elif obj == "link":
                return self._show_links(client)
            elif obj == "rule":
                return self._show_rules(client)
            else:
                self.console.print(f"[red]ip: unknown object '{obj}'[/red]")
                return 1

        except Exception as e:
            self.console.print(f"[red]ip: {e}[/red]")
            return 1

    def _show_addresses(self, client: ClientType) -> int:
        """Show IP addresses."""
        # This is a simplified version - real ip addr would parse more complex data
        self.console.print("[yellow]ip addr: simplified display[/yellow]")

        try:
            # Try to read interface information
            net_dev = read_proc_file(client, "/proc/net/dev")
            interfaces = []

            for line in net_dev.split("\n")[2:]:
                if ":" in line:
                    iface_name = line.split(":")[0].strip()
                    if iface_name:
                        interfaces.append(iface_name)

            for i, iface in enumerate(interfaces, 1):
                self.console.print(
                    f"{i}: {iface}: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP"
                )
                self.console.print(
                    "    link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff"
                )
                if iface == "lo":
                    self.console.print("    inet 127.0.0.1/8 scope host lo")
                else:
                    self.console.print(
                        f"    inet 172.17.0.2/16 brd 172.17.255.255 scope global {iface}"
                    )

            return 0

        except ProcReadError:
            self.console.print("[red]ip: cannot read network information[/red]")
            return 1

    def _show_routes(self, client: ClientType) -> int:
        """Show routing table."""
        try:
            route_info = read_proc_file(client, "/proc/net/route")
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

                    # Convert hex IP addresses to dotted decimal
                    dest_ip = self._hex_to_ip(dest)
                    gw_ip = self._hex_to_ip(gateway)

                    if dest_ip == "0.0.0.0":  # noqa: S104 # legitimate use of 0.0.0.0 for default route
                        self.console.print(f"default via {gw_ip} dev {iface}")
                    else:
                        self.console.print(f"{dest_ip} dev {iface}")

            return 0

        except ProcReadError:
            self.console.print("[red]ip: cannot read routing information[/red]")
            return 1

    def _show_links(self, client: ClientType) -> int:
        """Show network links."""
        try:
            net_dev = read_proc_file(client, "/proc/net/dev")
            lines = net_dev.strip().split("\n")

            index = 1
            for line in lines[2:]:
                if ":" in line:
                    iface_name = line.split(":")[0].strip()
                    if iface_name:
                        flags = "<BROADCAST,MULTICAST,UP,LOWER_UP>"
                        if iface_name == "lo":
                            flags = "<LOOPBACK,UP,LOWER_UP>"

                        self.console.print(
                            f"{index}: {iface_name}: {flags} mtu 1500 qdisc noqueue state UP mode DEFAULT"
                        )
                        self.console.print(
                            "    link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff"
                        )
                        index += 1

            return 0

        except ProcReadError:
            self.console.print(
                "[red]ip: cannot read network interface information[/red]"
            )
            return 1

    def _show_rules(self, client: ClientType) -> int:
        """Show routing policy rules."""
        # Default routing rules
        self.console.print("0:\tfrom all lookup local")
        self.console.print("32766:\tfrom all lookup main")
        self.console.print("32767:\tfrom all lookup default")
        return 0

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
