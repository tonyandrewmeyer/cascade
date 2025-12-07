"""Implementation of ifconfig command (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ...utils.command_helpers import parse_flags, safe_read_file
from ...utils.proc_reader import ProcReadError, read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class IfconfigCommand(Command):
    """Configure a network interface."""

    name = "ifconfig"
    help = "Configure a network interface"
    category = "Network Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Usage: ifconfig [-v] [-a] [-s] [interface]
       ifconfig [-v] interface [aftype] options | address ...

Configure a network interface.

Options:
    -a              Display all interfaces (even if down)
    -s              Display short list (like netstat -i)
    -v              Be more verbose for some error conditions
    -h, --help      Show this help message

Interface Options (not supported in container):
    up              Activate interface
    down            Deactivate interface
    [-]arp          Enable/disable ARP protocol
    [-]promisc      Enable/disable promiscuous mode
    [-]allmulti     Enable/disable all-multicast mode
    mtu N           Set Maximum Transfer Unit
    netmask addr    Set IP network mask
    broadcast addr  Set broadcast address
    hw class addr   Set hardware (MAC) address
    
Address Families:
    inet            TCP/IP (default)
    inet6           IPv6
    
Examples:
    ifconfig              # Show active interfaces
    ifconfig -a           # Show all interfaces
    ifconfig eth0         # Show specific interface
    ifconfig -s           # Short format
    
Note: Interface modification commands are not supported in container environment.
      This is a read-only version for viewing interface status.
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the ifconfig command."""
        # Parse arguments using common parsing code
        parse_result = parse_flags(
            args,
            {
                "a": bool,              # all interfaces
                "s": bool,              # short format
                "v": bool,              # verbose
                "h": bool,              # help
                "help": bool,
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result
            
        if flags["h"] or flags["help"]:
            self.show_help()
            return 0
            
        # Check for interface modification attempts
        if len(positional_args) > 1:
            # Check for common modification keywords
            modification_keywords = [
                "up", "down", "arp", "promisc", "allmulti", "mtu", 
                "netmask", "broadcast", "hw", "inet", "inet6"
            ]
            if any(keyword in positional_args[1:] for keyword in modification_keywords):
                self.shell.console.print("[red]ifconfig: interface modification not supported in container environment[/red]")
                self.shell.console.print("[yellow]This is a read-only version for viewing interface status.[/yellow]")
                return 1
                
        interface = positional_args[0] if positional_args else None
        show_all = flags["a"]
        short_format = flags["s"]
        verbose = flags["v"]

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
            if short_format:
                self._display_short_format(interfaces)
            else:
                for iface_name, stats in interfaces.items():
                    # Skip down interfaces unless -a is specified
                    if not show_all and not self._is_interface_up(client, iface_name):
                        continue
                        
                    self._display_interface(client, iface_name, stats, verbose)
                    if len(interfaces) > 1:
                        self.console.print()

            return 0

        except Exception as e:
            self.console.print(f"[red]ifconfig: {e}[/red]")
            return 1

    def _is_interface_up(self, client: ClientType, iface_name: str) -> bool:
        """Check if interface is up."""
        try:
            operstate_path = f"/sys/class/net/{iface_name}/operstate"
            operstate = safe_read_file(client, operstate_path, self.shell)
            return operstate and operstate.strip() == "up"
        except Exception:
            return False
            
    def _display_short_format(self, interfaces: dict):
        """Display interfaces in short format like netstat -i."""
        self.console.print("Kernel Interface table")
        self.console.print("Iface   MTU Met   RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg")
        
        for iface_name, stats in interfaces.items():
            # Format: interface name (8 chars), MTU, Metric, RX/TX stats, Flags
            iface_str = iface_name[:8].ljust(8)
            mtu_str = "1500".rjust(5)  # Default MTU
            met_str = "0".rjust(3)     # Metric
            
            rx_ok = str(stats['rx_packets']).rjust(7)
            rx_err = str(stats['rx_errors']).rjust(6)
            rx_drp = "0".rjust(6)      # Not available in /proc/net/dev
            rx_ovr = "0".rjust(6)
            
            tx_ok = str(stats['tx_packets']).rjust(8)
            tx_err = str(stats['tx_errors']).rjust(6)
            tx_drp = "0".rjust(6)
            tx_ovr = "0".rjust(6)
            
            flags = "BMU"  # Broadcast, Multicast, Up (simplified)
            
            line = f"{iface_str} {mtu_str} {met_str} {rx_ok} {rx_err} {rx_drp} {rx_ovr} {tx_ok} {tx_err} {tx_drp} {tx_ovr} {flags}"
            self.console.print(line)
            
    def _display_interface(self, client: ClientType, iface_name: str, stats: dict, verbose: bool = False):
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
