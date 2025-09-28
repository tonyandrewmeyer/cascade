"""Implementation of ifconfig command (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ...utils.command_helpers import handle_help_flag, safe_read_file
from ...utils.proc_reader import ProcReadError, read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

    from pebble_shell.shell import PebbleShell

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class IfconfigCommand(Command):
    """Implementation of ifconfig command (read-only)."""

    name = "ifconfig"
    help = "Display network interface configuration"
    category = "Network"

    def show_help(self):
        """Show command help."""
        help_text = """Display network interface configuration.

Usage: ifconfig [INTERFACE]

Description:
    Display configuration of network interfaces. Read-only version.

Options:
    -h, --help      Show this help message

Examples:
    ifconfig        # Show all interfaces
    ifconfig eth0   # Show specific interface
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the ifconfig command."""
        if handle_help_flag(self, args):
            return 0

        interface = args[0] if args else None

        try:
            # Read network interfaces from /proc/net/dev
            try:
                net_dev = read_proc_file(client, "/proc/net/dev")
            except ProcReadError:
                self.console.print(
                    "[red]ifconfig: cannot read network interface information[/red]"
                )
                return 1

            interfaces = {}
            lines = net_dev.strip().split("\n")

            # Skip header lines
            for line in lines[2:]:
                if ":" in line:
                    iface_name, stats = line.split(":", 1)
                    iface_name = iface_name.strip()

                    if interface and iface_name != interface:
                        continue

                    stats_values = stats.split()
                    if len(stats_values) >= 16:
                        interfaces[iface_name] = {
                            "rx_bytes": int(stats_values[0]),
                            "rx_packets": int(stats_values[1]),
                            "rx_errors": int(stats_values[2]),
                            "tx_bytes": int(stats_values[8]),
                            "tx_packets": int(stats_values[9]),
                            "tx_errors": int(stats_values[10]),
                        }

            if interface and interface not in interfaces:
                self.console.print(
                    f"[red]ifconfig: interface '{interface}' not found[/red]"
                )
                return 1

            # Display interface information
            for iface_name, stats in interfaces.items():
                self._display_interface(client, iface_name, stats)
                if len(interfaces) > 1:
                    self.console.print()

            return 0

        except Exception as e:
            self.console.print(f"[red]ifconfig: {e}[/red]")
            return 1

    def _display_interface(self, client: ClientType, iface_name: str, stats: dict):
        """Display information for a single interface."""
        self.console.print(f"[bold]{iface_name}[/bold]:", end="")

        # Try to get additional interface info
        flags = []
        try:
            # Check if interface is up
            operstate_path = f"/sys/class/net/{iface_name}/operstate"
            try:
                operstate = safe_read_file(client, operstate_path, self.shell)
                if operstate and operstate.strip() == "up":
                    flags.append("UP")
                else:
                    flags.append("DOWN")
            except Exception:
                # Broad exception needed for network interface probing
                flags.append("UNKNOWN")

            # Try to get MTU
            try:
                mtu_path = f"/sys/class/net/{iface_name}/mtu"
                mtu = safe_read_file(client, mtu_path, self.shell)
                mtu_value = mtu.strip() if mtu else "1500"
            except Exception:
                # Broad exception needed for network interface probing
                mtu_value = "1500"

            # Try to get MAC address
            try:
                addr_path = f"/sys/class/net/{iface_name}/address"
                mac_addr = safe_read_file(client, addr_path, self.shell)
                mac_addr = mac_addr.strip() if mac_addr else "00:00:00:00:00:00"
            except Exception:
                # Broad exception needed for network interface probing
                mac_addr = "00:00:00:00:00:00"

            flags.append("BROADCAST")
            flags.append("MULTICAST")

            self.console.print(f" flags=<{','.join(flags)}> mtu {mtu_value}")
            self.console.print(f"        ether {mac_addr}")

            # Display statistics
            self.console.print(
                f"        RX packets {stats['rx_packets']} bytes {stats['rx_bytes']} errors {stats['rx_errors']}"
            )
            self.console.print(
                f"        TX packets {stats['tx_packets']} bytes {stats['tx_bytes']} errors {stats['tx_errors']}"
            )

        except Exception:
            # Broad exception needed for network interface discovery
            self.console.print(" flags=<UNKNOWN>")
            self.console.print(
                f"        RX packets {stats['rx_packets']} bytes {stats['rx_bytes']}"
            )
            self.console.print(
                f"        TX packets {stats['tx_packets']} bytes {stats['tx_bytes']}"
            )
