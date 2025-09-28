"""Implementation of iplink command (read-only)."""

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


class IplinkCommand(Command):
    """Implementation of iplink command (read-only)."""

    name = "iplink"
    help = "Display network interfaces"
    category = "Network"

    def show_help(self):
        """Show command help."""
        help_text = """Display network interfaces.

Usage: iplink [OPTIONS]

Description:
    Display network interface information. Read-only version.
    Simplified version of 'ip link show'.

Options:
    -h, --help      Show this help message

Examples:
    iplink          # Show all network interfaces
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the iplink command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Read network interfaces from /proc/net/dev
            try:
                net_dev = read_proc_file(client, "/proc/net/dev")
            except ProcReadError:
                self.console.print(
                    "[red]iplink: cannot read network interface information[/red]"
                )
                return 1

            lines = net_dev.strip().split("\n")

            index = 1
            for line in lines[2:]:  # Skip header lines
                if ":" in line:
                    iface_name = line.split(":")[0].strip()
                    if iface_name:
                        # Get interface flags and info
                        try:
                            operstate_path = f"/sys/class/net/{iface_name}/operstate"
                            operstate = safe_read_file(
                                client, operstate_path, self.shell
                            )
                            state = (
                                "UP"
                                if operstate and operstate.strip() == "up"
                                else "DOWN"
                            )
                        except Exception:
                            # Broad exception needed for network interface probing
                            state = "UNKNOWN"

                        try:
                            mtu_path = f"/sys/class/net/{iface_name}/mtu"
                            mtu = safe_read_file(client, mtu_path, self.shell)
                            mtu_value = mtu.strip() if mtu else "1500"
                        except Exception:
                            # Broad exception needed for network interface probing
                            mtu_value = "1500"

                        try:
                            addr_path = f"/sys/class/net/{iface_name}/address"
                            mac_addr = safe_read_file(client, addr_path, self.shell)
                            mac_addr = (
                                mac_addr.strip() if mac_addr else "00:00:00:00:00:00"
                            )
                        except Exception:
                            # Broad exception needed for network interface probing
                            mac_addr = "00:00:00:00:00:00"

                        flags = "BROADCAST,MULTICAST"
                        if state == "UP":
                            flags += ",UP,LOWER_UP"
                        if iface_name == "lo":
                            flags = "LOOPBACK,UP,LOWER_UP"

                        self.console.print(
                            f"{index}: {iface_name}: <{flags}> mtu {mtu_value} qdisc noqueue state {state}"
                        )
                        self.console.print(
                            f"    link/ether {mac_addr} brd ff:ff:ff:ff:ff:ff"
                        )
                        index += 1

            return 0

        except Exception as e:
            self.console.print(f"[red]iplink: {e}[/red]")
            return 1
