"""Show routing table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from rich.panel import Panel

from ...utils.command_helpers import parse_flags
from ...utils.proc_reader import parse_proc_route
from ...utils.table_builder import create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class RouteCommand(Command):
    """Manipulate the kernel's IP routing tables."""

    name = "route"
    help = "Manipulate the kernel's IP routing tables"
    category = "Network Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Usage: route [options] [command [target [netmask [gw [interface]]]]]

Manipulate the kernel's IP routing tables.

Options:
    -A family           Use specified address family (default: inet)
    -F                  Operate on FIB (default)
    -C                  Operate on routing cache
    -v, --verbose       Verbose operation
    -n                  Don't resolve hostnames
    -e                  Use netstat-format for display
    -4                  IPv4 mode
    -6                  IPv6 mode
    -h, --help          Show this help message

Commands:
    add                 Add new route
    del                 Delete route
    (none)              Display routing table

Modifiers for add/del:
    -net                Target is a network
    -host               Target is a host
    netmask NM          Network mask
    gw GW               Gateway address
    metric M            Set metric
    dev IF              Force route to interface
    reject              Install blocking route
    mss M               Set MSS (bytes)
    window W            Set TCP window size
    
Note: Route modification commands are not supported in container environment.
      Use 'ip route' commands on the host system instead.
        """
        self.shell.console.print(help_text)

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute route command."""
        # Parse arguments using common parsing code
        parse_result = parse_flags(
            args,
            {
                "A": str,              # address family
                "F": bool,             # FIB
                "C": bool,             # cache
                "v": bool,             # verbose
                "verbose": bool,
                "n": bool,             # numeric
                "e": bool,             # netstat format
                "4": bool,             # IPv4
                "6": bool,             # IPv6
                "h": bool,             # help
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
            
        # Handle IPv6 mode
        if flags["6"]:
            self.shell.console.print("[yellow]route: IPv6 routing table display not yet implemented.[/yellow]")
            return 0
            
        # Handle cache mode
        if flags["C"]:
            self.shell.console.print("[yellow]route: Routing cache display not supported in container environment.[/yellow]")
            return 0
            
        # Check for route modification commands
        if positional_args and positional_args[0] in ["add", "del", "delete"]:
            self.shell.console.print("[red]route: Route modification not supported in container environment.[/red]")
            self.shell.console.print("[yellow]Use 'ip route' commands on the host system instead.[/yellow]")
            return 1
            
        # Display routing table
        try:
            routes = parse_proc_route(client)
            self._display_routes(routes, flags)
        except Exception as e:
            if flags["v"] or flags["verbose"]:
                self.shell.console.print(f"[red]route: error reading routing table: {e}[/red]")
            else:
                self.shell.console.print("[red]route: error reading routing table[/red]")
            return 1
            
        return 0
        
    def _display_routes(self, routes: list[dict], flags: dict):
        """Display routing table in specified format."""
        if flags["e"]:
            # Netstat format
            self._display_netstat_format(routes, flags)
        else:
            # Standard route format
            self._display_standard_format(routes, flags)
            
    def _display_standard_format(self, routes: list[dict], flags: dict):
        """Display routing table in standard route format."""
        table = create_standard_table()
        table.add_column("Destination", style="cyan", no_wrap=True)
        table.add_column("Gateway", style="blue", no_wrap=True)
        table.add_column("Genmask", style="magenta", no_wrap=True)
        table.add_column("Flags", style="yellow", no_wrap=True)
        table.add_column("Metric", style="green", no_wrap=True, justify="right")
        table.add_column("Ref", style="white", no_wrap=True, justify="right")
        table.add_column("Use", style="white", no_wrap=True, justify="right")
        table.add_column("Iface", style="cyan", no_wrap=True)

        for route in routes:
            table.add_row(
                route["destination"],
                route["gateway"],
                route["mask"],
                route["flags"],
                route["metric"],
                route.get("ref", "0"),
                route.get("use", "0"),
                route["interface"],
            )

        title = "Kernel IP routing table"
        if flags["v"] or flags["verbose"]:
            title += " (verbose)"
            
        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text(title),
                style=get_theme().info,
            )
        )
        
    def _display_netstat_format(self, routes: list[dict], flags: dict):
        """Display routing table in netstat format."""
        self.shell.console.print("\n[bold]Kernel IP routing table[/bold]")
        self.shell.console.print("Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface")
        
        for route in routes:
            dest = route["destination"].ljust(15)
            gw = route["gateway"].ljust(15)
            mask = route["mask"].ljust(15)
            flags_str = route["flags"].ljust(7)
            mss = "0".rjust(5)
            window = "0".rjust(6)
            irtt = "0".rjust(5)
            iface = route["interface"]
            
            line = f"{dest} {gw} {mask} {flags_str} {mss} {window} {irtt} {iface}"
            self.shell.console.print(line)
