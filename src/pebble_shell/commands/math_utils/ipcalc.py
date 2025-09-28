"""Implementation of IpcalcCommand."""

from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class IpcalcCommand(Command):
    """Implementation of ipcalc command."""

    name = "ipcalc"
    help = "IP network calculator"
    category = "Mathematical Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """IP network calculator.

Usage: ipcalc [OPTIONS] ADDRESS[/PREFIX]

Description:
    Calculate network information for IP addresses and networks.

Options:
    -n, --network       Display network address
    -b, --broadcast     Display broadcast address
    -m, --netmask       Display network mask
    -p, --prefix        Display prefix length
    -c, --class         Display address class
    -h, --hostmask      Display host mask
    -f, --first         Display first host address
    -l, --last          Display last host address
    --hosts             Display number of hosts
    --help              Show this help message

Examples:
    ipcalc 192.168.1.100/24
    ipcalc -n -b 10.0.0.1/8
    ipcalc --hosts 172.16.0.0/16
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the ipcalc command."""
        if handle_help_flag(self, args):
            return 0

        # TODO: Can this use the common flag parser?
        parse_result = parse_flags(
            args,
            {
                "n": bool,  # network
                "network": bool,
                "b": bool,  # broadcast
                "broadcast": bool,
                "m": bool,  # netmask
                "netmask": bool,
                "p": bool,  # prefix
                "prefix": bool,
                "c": bool,  # class
                "class": bool,
                "h": bool,  # hostmask
                "hostmask": bool,
                "f": bool,  # first host
                "first": bool,
                "l": bool,  # last host
                "last": bool,
                "hosts": bool,  # number of hosts
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if not positional_args:
            self.console.print("[red]ipcalc: missing IP address[/red]")
            return 1

        address_input = positional_args[0]

        try:
            # Parse IP address/network.
            if "/" in address_input:
                network = ipaddress.ip_network(address_input, strict=False)
                address = network.network_address
            else:
                # Default to /32 for single IP.
                address = ipaddress.ip_address(address_input)
                network = ipaddress.ip_network(f"{address}/32", strict=False)

            # Determine what to show:
            show_network = flags.get("n", False) or flags.get("network", False)
            show_broadcast = flags.get("b", False) or flags.get("broadcast", False)
            show_netmask = flags.get("m", False) or flags.get("netmask", False)
            show_prefix = flags.get("p", False) or flags.get("prefix", False)
            show_class = flags.get("c", False) or flags.get("class", False)
            show_hostmask = flags.get("h", False) or flags.get("hostmask", False)
            show_first = flags.get("f", False) or flags.get("first", False)
            show_last = flags.get("l", False) or flags.get("last", False)
            show_hosts = flags.get("hosts", False)

            # If no specific flags, show everything.
            show_all = not any(
                [
                    show_network,
                    show_broadcast,
                    show_netmask,
                    show_prefix,
                    show_class,
                    show_hostmask,
                    show_first,
                    show_last,
                    show_hosts,
                ]
            )

            if show_all or show_network:
                self.console.print(
                    f"Network:   {network.network_address}/{network.prefixlen}"
                )

            if (show_all or show_netmask) and isinstance(
                network, ipaddress.IPv4Network | ipaddress.IPv6Network
            ):
                self.console.print(f"Netmask:   {network.netmask}")

            if (show_all or show_broadcast) and isinstance(
                network, ipaddress.IPv4Network
            ):
                self.console.print(f"Broadcast: {network.broadcast_address}")

            if show_all or show_hostmask:
                if isinstance(network, ipaddress.IPv4Network):
                    hostmask = ipaddress.IPv4Address(int(network.netmask) ^ (2**32 - 1))
                    self.console.print(f"HostMask:  {hostmask}")
                else:
                    hostmask_int = (2**network.max_prefixlen - 1) ^ (
                        2 ** (network.max_prefixlen - network.prefixlen) - 1
                    )
                    hostmask = ipaddress.IPv6Address(hostmask_int ^ (2**128 - 1))
                    self.console.print(f"HostMask:  {hostmask}")

            if show_all or show_prefix:
                self.console.print(f"Prefix:    /{network.prefixlen}")

            if (show_all or show_class) and isinstance(address, ipaddress.IPv4Address):
                addr_class = self._get_ipv4_class(address)
                self.console.print(f"Class:     {addr_class}")

            if show_all or show_first:
                if network.num_addresses > 2:
                    first_host = next(iter(network.hosts()))
                    self.console.print(f"First:     {first_host}")
                elif network.num_addresses == 1:
                    self.console.print(f"First:     {network.network_address}")

            if show_all or show_last:
                if network.num_addresses > 2:
                    last_host = list(network.hosts())[-1]
                    self.console.print(f"Last:      {last_host}")
                elif network.num_addresses == 1:
                    self.console.print(f"Last:      {network.network_address}")

            if show_all or show_hosts:
                num_hosts = network.num_addresses
                if (
                    isinstance(network, ipaddress.IPv4Network)
                    and network.prefixlen < 31
                ):
                    num_hosts -= 2  # Subtract network and broadcast
                self.console.print(f"Hosts:     {num_hosts}")

            return 0

        except ValueError as e:
            self.console.print(f"[red]ipcalc: invalid IP address or network: {e}[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]ipcalc: {e}[/red]")
            return 1

    def _get_ipv4_class(self, address: ipaddress.IPv4Address) -> str:
        """Get IPv4 address class."""
        first_octet = address.packed[0]

        if first_octet < 128:
            return "A"
        elif first_octet < 192:
            return "B"
        elif first_octet < 224:
            return "C"
        elif first_octet < 240:
            return "D (multicast)"
        else:
            return "E (reserved)"
