"""Show socket statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from rich.panel import Panel
from rich.table import Table

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


class SocketStatsCommand(Command):
    """Another utility to investigate sockets."""

    name = "ss"
    help = "Another utility to investigate sockets"
    category = "Network Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Usage: ss [options] [filter]

Another utility to investigate sockets.

Options:
    -h, --help          Show this message
    -V, --version       Output version information
    -n, --numeric       Don't resolve service names
    -r, --resolve       Resolve host names
    -a, --all           Display all sockets
    -l, --listening     Display listening sockets
    -o, --options       Show timer information
    -e, --extended      Show detailed socket information
    -m, --memory        Show socket memory usage
    -p, --processes     Show process using socket
    -T, --threads       Show thread using socket
    -i, --info          Show internal TCP information
    -s, --summary       Show socket usage summary
    -b, --bpf           Show bpf filter socket information
    -E, --events        Continually display sockets as they are destroyed
    -Z, --context       Display task SELinux security contexts
    -z, --contexts      Display task and socket SELinux security contexts
    -N, --net           Switch to the specified network namespace name
    
    -4, --ipv4          Display only IP version 4 sockets
    -6, --ipv6          Display only IP version 6 sockets
    -0, --packet        Display PACKET sockets
    -t, --tcp           Display only TCP sockets
    -M, --mptcp         Display only MPTCP sockets
    -S, --sctp          Display only SCTP sockets
    -u, --udp           Display only UDP sockets
    -d, --dccp          Display only DCCP sockets
    -w, --raw           Display only RAW sockets
    -x, --unix          Display only Unix domain sockets
    --tipc              Display only TIPC sockets
    --vsock             Display only vsock sockets
    --xdp               Display only XDP sockets
    
    -f, --family=FAMILY Display sockets of type FAMILY
    -A, --query=QUERY   Query specific socket types
    -K, --kill          Forcibly close sockets
    -H, --no-header     Suppress header line
    -O, --oneline       Socket's data printed on a single line
    
Note: This command shows information from the remote container environment.
      Some options may not be available in container context.
        """
        self.shell.console.print(help_text)

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute ss command."""
        # Parse arguments using common parsing code
        parse_result = parse_flags(
            args,
            {
                "h": bool,              # help
                "help": bool,
                "V": bool,              # version
                "version": bool,
                "n": bool,              # numeric
                "numeric": bool,
                "r": bool,              # resolve
                "resolve": bool,
                "a": bool,              # all
                "all": bool,
                "l": bool,              # listening
                "listening": bool,
                "o": bool,              # options
                "options": bool,
                "e": bool,              # extended
                "extended": bool,
                "m": bool,              # memory
                "memory": bool,
                "p": bool,              # processes
                "processes": bool,
                "T": bool,              # threads
                "threads": bool,
                "i": bool,              # info
                "info": bool,
                "s": bool,              # summary
                "summary": bool,
                "b": bool,              # bpf
                "bpf": bool,
                "E": bool,              # events
                "events": bool,
                "Z": bool,              # context
                "context": bool,
                "z": bool,              # contexts
                "contexts": bool,
                "N": str,               # net namespace
                "net": str,
                "4": bool,              # ipv4
                "ipv4": bool,
                "6": bool,              # ipv6
                "ipv6": bool,
                "0": bool,              # packet
                "packet": bool,
                "t": bool,              # tcp
                "tcp": bool,
                "M": bool,              # mptcp
                "mptcp": bool,
                "S": bool,              # sctp
                "sctp": bool,
                "u": bool,              # udp
                "udp": bool,
                "d": bool,              # dccp
                "dccp": bool,
                "w": bool,              # raw
                "raw": bool,
                "x": bool,              # unix
                "unix": bool,
                "f": str,               # family
                "family": str,
                "A": str,               # query
                "query": str,
                "K": bool,              # kill
                "kill": bool,
                "H": bool,              # no-header
                "no-header": bool,
                "O": bool,              # oneline
                "oneline": bool,
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result
            
        if flags["h"] or flags["help"]:
            self.show_help()
            return 0
            
        if flags["V"] or flags["version"]:
            self.shell.console.print("ss utility, pebble-shell version")
            return 0
            
        # Handle unsupported options in container environment
        if flags["K"] or flags["kill"]:
            self.shell.console.print("[red]ss: socket killing not supported in container environment[/red]")
            return 1
            
        if flags["E"] or flags["events"]:
            self.shell.console.print("[red]ss: event monitoring not supported in container environment[/red]")
            return 1
            
        if flags["N"] or flags["net"]:
            self.shell.console.print("[yellow]ss: network namespace switching not supported in container environment[/yellow]")
            return 0
            
        if flags["Z"] or flags["context"] or flags["z"] or flags["contexts"]:
            self.shell.console.print("[yellow]ss: SELinux context display not available in container environment[/yellow]")
            return 0
            
        # Handle summary mode
        if flags["s"] or flags["summary"]:
            return self._show_summary(client, flags)
            
        # Determine which socket types to show
        protocols = self._get_protocols(flags)
        
        # Show socket information
        return self._show_sockets(client, protocols, flags)
        
    def _get_protocols(self, flags: dict) -> list[str]:
        """Determine which protocols to display based on flags."""
        protocols = []
        
        if flags["t"] or flags["tcp"]:
            protocols.append("tcp")
        if flags["u"] or flags["udp"]:
            protocols.append("udp")
        if flags["w"] or flags["raw"]:
            protocols.append("raw")
        if flags["x"] or flags["unix"]:
            protocols.append("unix")
        if flags["0"] or flags["packet"]:
            protocols.append("packet")
            
        # Handle family specification
        family = flags.get("f") or flags.get("family")
        if family:
            if family == "inet":
                protocols = ["tcp", "udp"]
            elif family == "inet6":
                protocols = ["tcp6", "udp6"]
            elif family == "unix":
                protocols = ["unix"]
            elif family == "packet":
                protocols = ["packet"]
                
        # Default to TCP if no protocols specified
        if not protocols:
            protocols = ["tcp"]
            
        return protocols
        
    def _show_summary(self, client, flags: dict) -> int:
        """Show socket usage summary."""
        try:
            # Count sockets by type
            tcp_count = len(parse_proc_net_connections(client, "tcp"))
            udp_count = len(parse_proc_net_connections(client, "udp")) 
            unix_count = len(parse_proc_net_connections(client, "unix"))
            
            self.shell.console.print("Total: 0")
            self.shell.console.print(f"TCP:   {tcp_count}")
            self.shell.console.print(f"UDP:   {udp_count}")
            self.shell.console.print(f"RAW:   0")
            self.shell.console.print(f"FRAG:  0")
            self.shell.console.print(f"UNIX:  {unix_count}")
            
        except ProcReadError as e:
            self.shell.console.print(f"[red]ss: error reading socket information: {e}[/red]")
            return 1
            
        return 0
        
    def _show_sockets(self, client, protocols: list[str], flags: dict) -> int:
        """Show detailed socket information."""
        show_all = flags["a"] or flags["all"]
        show_listening = flags["l"] or flags["listening"]
        numeric = flags["n"] or flags["numeric"]
        extended = flags["e"] or flags["extended"]
        no_header = flags["H"] or flags["no-header"]
        oneline = flags["O"] or flags["oneline"]
        
        all_sockets = []
        
        for protocol in protocols:
            try:
                connections = parse_proc_net_connections(client, protocol)
                
                # Filter based on listening/all flags
                if show_listening:
                    connections = [c for c in connections if c.get('state') == 'LISTEN']
                elif not show_all:
                    # Default: show non-listening connections
                    connections = [c for c in connections if c.get('state') != 'LISTEN']
                    
                for conn in connections:
                    conn['protocol'] = protocol
                    all_sockets.append(conn)
                    
            except ProcReadError:
                if flags["v"] or flags["verbose"]:
                    self.shell.console.print(f"[yellow]ss: could not read {protocol} sockets[/yellow]")
                    
        if not all_sockets:
            return 0
            
        # Display sockets
        if oneline:
            self._display_oneline(all_sockets, flags)
        else:
            self._display_table(all_sockets, flags)
            
        return 0
        
    def _display_table(self, sockets: list[dict], flags: dict):
        """Display sockets in table format."""
        table = Table(show_header=not (flags["H"] or flags["no-header"]), 
                     header_style="bold blue")
                     
        table.add_column("Netid", style="cyan", no_wrap=True)
        table.add_column("State", style="yellow", no_wrap=True)
        table.add_column("Recv-Q", style="green", no_wrap=True, justify="right")
        table.add_column("Send-Q", style="green", no_wrap=True, justify="right")
        table.add_column("Local Address:Port", style="blue", no_wrap=True)
        table.add_column("Peer Address:Port", style="magenta", no_wrap=True)
        
        if flags["p"] or flags["processes"]:
            table.add_column("Process", style="white", no_wrap=True)
            
        for sock in sockets:
            row = [
                sock.get('protocol', 'tcp').upper(),
                sock.get('state', ''),
                sock.get('rx_queue', '0'),
                sock.get('tx_queue', '0'),
                sock.get('local_address', ''),
                sock.get('remote_address', ''),
            ]
            
            if flags["p"] or flags["processes"]:
                row.append("-")  # Process info not available in container
                
            table.add_row(*row)
            
        if sockets:
            self.shell.console.print(table)
            
    def _display_oneline(self, sockets: list[dict], flags: dict):
        """Display sockets in one-line format."""
        for sock in sockets:
            protocol = sock.get('protocol', 'tcp').upper()
            state = sock.get('state', '')
            local = sock.get('local_address', '')
            remote = sock.get('remote_address', '')
            
            line = f"{protocol} {state} {local} {remote}"
            if flags["p"] or flags["processes"]:
                line += " -"
                
            self.shell.console.print(line)
