"""Show network connections."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from rich.panel import Panel

from ...utils.command_helpers import parse_flags
from ...utils.proc_reader import ProcReadError, parse_proc_net_connections
from ...utils.table_builder import create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class NetstatCommand(Command):
    """Print network connections, routing tables, interface statistics, masquerade connections, and multicast memberships."""

    name = "netstat"
    help = "Print network connections, routing tables, interface statistics"
    category = "Network Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Usage: netstat [address_family_options] [--tcp|-t] [--udp|-u] [--raw|-w] [--unix|-x]
                [--listening|-l] [--all|-a] [--numeric|-n] [--numeric-hosts]
                [--numeric-ports] [--numeric-users] [--symbolic|-N] [--extend|-e]
                [--timers|-o] [--program|-p] [--verbose|-v] [--continuous|-c] [--wide|-W]
                [--route|-r] [--groups|-g] [--interfaces|-i] [--statistics|-s]

Print network connections, routing tables, interface statistics.

Options:
    -a, --all               Show both listening and non-listening sockets
    -l, --listening         Show only listening sockets
    -n, --numeric          Show numerical addresses instead of resolving hosts
    --numeric-hosts        Show numerical host addresses but resolve other names
    --numeric-ports        Show numerical port numbers but resolve other names
    --numeric-users        Show numerical user IDs but resolve other names
    -p, --program          Show the PID and name of the program to which each socket belongs
    -t, --tcp              Show TCP connections
    -u, --udp              Show UDP connections
    -w, --raw              Show raw connections
    -x, --unix             Show Unix domain sockets
    -r, --route            Display kernel routing tables
    -i, --interfaces       Display network interface table
    -g, --groups           Display multicast group memberships
    -s, --statistics       Display networking statistics
    -e, --extend           Display additional information
    -v, --verbose          Be verbose
    -c, --continuous       Display information continuously
    -W, --wide             Don't truncate IP addresses
    -h, --help             Show this help message

Note: This command shows information from the remote container environment.
        """
        self.shell.console.print(help_text)

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute netstat command."""
        # Parse arguments using common parsing code
        parse_result = parse_flags(
            args,
            {
                "a": bool,              # all
                "all": bool,
                "l": bool,              # listening
                "listening": bool,
                "n": bool,              # numeric
                "numeric": bool,
                "numeric-hosts": bool,
                "numeric-ports": bool,
                "numeric-users": bool,
                "p": bool,              # program
                "program": bool,
                "t": bool,              # tcp
                "tcp": bool,
                "u": bool,              # udp
                "udp": bool,
                "w": bool,              # raw
                "raw": bool,
                "x": bool,              # unix
                "unix": bool,
                "r": bool,              # route
                "route": bool,
                "i": bool,              # interfaces
                "interfaces": bool,
                "g": bool,              # groups
                "groups": bool,
                "s": bool,              # statistics
                "statistics": bool,
                "e": bool,              # extend
                "extend": bool,
                "v": bool,              # verbose
                "verbose": bool,
                "c": bool,              # continuous
                "continuous": bool,
                "W": bool,              # wide
                "wide": bool,
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
            
        # Handle special modes
        if flags["r"] or flags["route"]:
            self.shell.console.print("[yellow]netstat: --route mode not yet implemented. Use 'route' command.[/yellow]")
            return 0
            
        if flags["i"] or flags["interfaces"]:
            self.shell.console.print("[yellow]netstat: --interfaces mode not yet implemented. Use 'ifconfig' command.[/yellow]")
            return 0
            
        if flags["g"] or flags["groups"]:
            self.shell.console.print("[yellow]netstat: --groups mode not yet implemented.[/yellow]")
            return 0
            
        if flags["s"] or flags["statistics"]:
            self.shell.console.print("[yellow]netstat: --statistics mode not yet implemented.[/yellow]")
            return 0
            
        if flags["c"] or flags["continuous"]:
            self.shell.console.print("[yellow]netstat: --continuous mode not supported in this environment.[/yellow]")
            return 0
            
        # Determine protocols to show
        protocols = []
        if flags["t"] or flags["tcp"]:
            protocols.append("tcp")
        if flags["u"] or flags["udp"]:
            protocols.append("udp")
        if flags["w"] or flags["raw"]:
            protocols.append("raw")
        if flags["x"] or flags["unix"]:
            protocols.append("unix")
            
        # Default to TCP if no protocols specified
        if not protocols:
            protocols = ["tcp"]
            
        # Show connections for each protocol
        for protocol in protocols:
            try:
                connections = parse_proc_net_connections(client, protocol)
                
                # Filter based on listening/all flags
                if flags["l"] or flags["listening"]:
                    # Show only listening connections
                    connections = [c for c in connections if c.get('state') == 'LISTEN']
                elif not (flags["a"] or flags["all"]):
                    # Default: show non-listening connections
                    connections = [c for c in connections if c.get('state') != 'LISTEN']
                # If -a/--all is specified, show all connections (no filtering)
                
                if connections:
                    self._display_connections(connections, protocol, flags)
                elif flags["v"] or flags["verbose"]:
                    self.shell.console.print(f"No {protocol} connections found")
                    
            except ProcReadError as e:
                if flags["v"] or flags["verbose"]:
                    self.shell.console.print(f"Error reading {protocol} connections: {e}")
                
        return 0

    def _display_connections(self, connections: list[dict[str, str]], protocol: str, flags: dict):
        """Display network connections in a formatted table."""
        if protocol == "unix":
            self._display_unix_connections(connections, flags)
        else:
            self._display_inet_connections(connections, protocol, flags)

    def _display_inet_connections(
        self, connections: list[dict[str, str]], protocol: str, flags: dict
    ):
        """Display TCP/UDP connections."""
        table = create_standard_table()

        # Add columns based on protocol and flags
        table.add_column("Proto", style="cyan", no_wrap=True)
        table.add_column("Recv-Q", style="yellow", no_wrap=True, justify="right")
        table.add_column("Send-Q", style="yellow", no_wrap=True, justify="right")
        table.primary_id_column("Local Address")
        table.primary_id_column("Foreign Address")
        table.status_column("State")
        
        # Add PID/Program column if requested
        if flags["p"] or flags["program"]:
            table.add_column("PID/Program name", style="green", no_wrap=True)

        for connection in connections:
            row = [
                protocol.upper(),
                connection.get("rx_queue", "0"),
                connection.get("tx_queue", "0"),
                connection["local_address"],
                connection["remote_address"],
                connection.get("state", ""),
            ]
            
            if flags["p"] or flags["program"]:
                # PID/Program info not available from /proc in container
                row.append("-")

            table.add_row(*row)

        # Show protocol header if multiple protocols
        header = f"Active Internet connections"
        if flags["l"] or flags["listening"]:
            header += " (only servers)"
        elif not (flags["a"] or flags["all"]):
            header += " (w/o servers)"
            
        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text(header),
                style=get_theme().info,
            )
        )

    def _display_unix_connections(self, connections: list[dict[str, str]], flags: dict):
        """Display UNIX domain sockets."""
        table = create_standard_table()
        table.add_column("Proto", style="cyan", no_wrap=True)
        table.add_column("RefCnt", style="yellow", no_wrap=True, justify="right")
        table.add_column("Flags", style="magenta", no_wrap=True)
        table.add_column("Type", style="cyan", no_wrap=True)
        table.status_column("State")
        table.add_column("I-Node", style="blue", no_wrap=True, justify="right")
        table.data_column("Path")
        
        # Add PID/Program column if requested
        if flags["p"] or flags["program"]:
            table.add_column("PID/Program name", style="green", no_wrap=True)

        for connection in connections:
            row = [
                "unix",
                connection.get("refcnt", "0"),
                connection.get("flags", ""),
                connection.get("type", ""),
                connection.get("state", ""),
                connection.get("inode", ""),
                connection.get("path", ""),
            ]
            
            if flags["p"] or flags["program"]:
                row.append("-")

            table.add_row(*row)

        header = "Active UNIX domain sockets"
        if flags["l"] or flags["listening"]:
            header += " (only servers)"
        elif not (flags["a"] or flags["all"]):
            header += " (w/o servers)"
            
        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text(header),
                style=get_theme().info,
            )
        )
