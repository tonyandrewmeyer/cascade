"""Show ARP table."""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Union

from rich.panel import Panel
from rich.table import Table

from ...utils.command_helpers import parse_flags
from ...utils.proc_reader import parse_proc_arp
from ...utils.table_builder import create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class ArpCommand(Command):
    """Show ARP table."""

    name = "arp"
    help = "Manipulate or display the kernel's IPv4 network neighbour cache"
    category = "Network Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute arp command."""
        parse_result = parse_flags(
            args,
            {
                "a": bool,        # BSD-style output
                "e": bool,        # Linux-style output
                "v": bool,        # verbose
                "verbose": bool,
                "n": bool,        # numeric
                "numeric": bool,
                "i": str,         # interface
                "interface": str,
                "d": str,         # delete
                "delete": str,
                "s": str,         # set
                "set": str,
                "H": str,         # hw-type
                "hw-type": str,
                "h": bool,        # help
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
            
        if flags["d"] or flags["delete"]:
            self.shell.console.print("[red]arp: delete operation not supported[/red]")
            return 1
            
        if flags["s"] or flags["set"]:
            self.shell.console.print("[red]arp: set operation not supported[/red]")
            return 1
            
        arp_entries = parse_proc_arp(client)
            
        interface = flags["i"] or flags["interface"]
        if interface:
            arp_entries = [e for e in arp_entries if e['device'] == interface]
            
        hostname = positional_args[0] if positional_args else None
        if hostname:
            numeric_mode = flags["n"] or flags["numeric"]
            target_ip = self._resolve_hostname(hostname, not numeric_mode)
            if target_ip:
                arp_entries = [e for e in arp_entries if e['ip_address'] == target_ip]
            else:
                arp_entries = [e for e in arp_entries if e['ip_address'] == hostname]
                
        if not arp_entries and hostname:
            self.shell.console.print(f"[red]arp: {hostname}: no entry[/red]")
            return 1
            
        if flags["a"]:
            self._display_bsd_format(arp_entries, flags)
        else:
            self._display_linux_format(arp_entries, flags)
            
        return 0

    def show_help(self):
        """Show command help."""
        help_text = """Usage: arp [options] [hostname]
       arp [-v] [-i if] -d hostname [pub]
       arp [-v] [-H type] [-i if] -s hostname hw_addr [temp]

Manipulate or display the kernel's IPv4 network neighbour cache.

Options:
    -a               Use BSD-style output format
    -e               Use Linux-style output format (default)
    -v, --verbose    Be verbose
    -n, --numeric    Don't resolve hosts
    -i if            Select interface
    -d               Delete entry
    -s               Set entry
    -H type          Hardware address type (default: ether)
    -h, --help       Show this help message

Note: Entry modification (-d, -s) requires administrative privileges.
        """
        self.shell.console.print(help_text)

    def _resolve_hostname(self, hostname: str, resolve: bool) -> str | None:
        """Resolve hostname to IP address."""
        if not resolve:
            return hostname
            
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None
            
    def _display_bsd_format(self, arp_entries: list, flags: dict):
        """Display ARP entries in BSD format."""
        for entry in arp_entries:
            hostname = entry['ip_address']
            numeric_mode = flags["n"] or flags["numeric"]
            if not numeric_mode:
                try:
                    hostname = socket.gethostbyaddr(entry['ip_address'])[0]
                except socket.herror:
                    pass
                    
            hwaddr = entry['hw_address'] if entry['hw_address'] != '00:00:00:00:00:00' else '(incomplete)'
            arp_flags = self._format_flags_bsd(entry['flags'])
            interface = entry['device']
            
            output = f"{hostname} ({entry['ip_address']}) at {hwaddr}"
            if arp_flags:
                output += f" [{arp_flags}]"
            output += f" on {interface}"
            
            verbose_mode = flags["v"] or flags["verbose"]
            if verbose_mode:
                output += f" hwtype {entry['hw_type']} mask {entry['mask']}"
                
            self.shell.console.print(output)
            
    def _display_linux_format(self, arp_entries: list, flags: dict):
        """Display ARP entries in Linux format with pretty output."""
        numeric_mode = flags["n"] or flags["numeric"]
        
        if numeric_mode or not arp_entries:
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Address", style="cyan")
            table.add_column("HWtype", style="magenta")
            table.add_column("HWaddress", style="green")
            table.add_column("Flags", style="yellow")
            table.add_column("Mask", style="blue")
            table.add_column("Iface", style="cyan")
            
            for entry in arp_entries:
                table.add_row(
                    entry['ip_address'],
                    entry['hw_type'],
                    entry['hw_address'],
                    entry['flags'],
                    entry['mask'],
                    entry['device']
                )
                
            if arp_entries:
                self.shell.console.print(
                    Panel(
                        table,
                        title=get_theme().highlight_text("ARP Table"),
                        style=get_theme().info,
                    )
                )
        else:
            table = create_standard_table()
            table.primary_id_column("Address")
            table.secondary_column("HWtype")
            table.data_column("HWaddress", no_wrap=True)
            table.status_column("Flags")
            table.secondary_column("Mask")
            table.primary_id_column("Iface")
            
            for entry in arp_entries:
                hostname = entry['ip_address']
                if not numeric_mode:
                    try:
                        hostname = socket.gethostbyaddr(entry['ip_address'])[0]
                    except socket.herror:
                        pass
                        
                table.add_row(
                    hostname,
                    entry['hw_type'],
                    entry['hw_address'],
                    entry['flags'],
                    entry['mask'],
                    entry['device']
                )
                
            self.shell.console.print(
                Panel(
                    table.build(),
                    title=get_theme().highlight_text("ARP Table"),
                    style=get_theme().info,
                )
            )
            
    def _format_flags_bsd(self, flags: str) -> str:
        """Format flags for BSD output style."""
        flag_map = {
            'C': 'complete',
            'M': 'permanent', 
            'P': 'published'
        }
        
        result = []
        for flag in flags:
            if flag in flag_map:
                result.append(flag_map[flag])
                
        return ','.join(result)
