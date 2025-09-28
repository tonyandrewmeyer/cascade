"""Show network connections."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
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
    """Show network connections."""

    name = "netstat"
    help = "Show network connections (default: tcp)"
    category = "Network Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute netstat command."""
        if handle_help_flag(self, args):
            return 0
        protocol = "tcp"
        if args and args[0] in ["tcp", "udp", "unix"]:
            protocol = args[0]

        try:
            connections = parse_proc_net_connections(client, protocol)
            self._display_connections(connections, protocol)
        except ProcReadError as e:
            self.shell.console.print(f"Error reading network connections: {e}")
            return 1
        return 0

    def _display_connections(self, connections: list[dict[str, str]], protocol: str):
        """Display network connections in a formatted table."""
        if protocol == "unix":
            self._display_unix_connections(connections)
        else:
            self._display_inet_connections(connections, protocol)

    def _display_inet_connections(
        self, connections: list[dict[str, str]], protocol: str
    ):
        """Display TCP/UDP connections."""
        table = create_standard_table()

        # Add columns based on protocol
        table.primary_id_column("Local Address")
        table.primary_id_column("Remote Address")
        if protocol == "tcp":
            table.status_column("State")

        for connection in connections:
            row = [
                connection["local_address"],  # Theme handled by column style
                connection["remote_address"],  # Theme handled by column style
            ]
            if protocol == "tcp" and "state" in connection:
                row.append(connection["state"])  # Theme handled by column style

            table.add_row(*row)

        header = f"{protocol.upper()} Connections:"
        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text(header),
                style=get_theme().info,
            )
        )

    def _display_unix_connections(self, connections: list[dict[str, str]]):
        """Display UNIX domain sockets."""
        table = create_standard_table()
        table.status_column("Type")
        table.status_column("State")
        table.data_column("Path")

        for connection in connections:
            table.add_row(
                connection["type"],  # Theme handled by column style
                connection["state"],  # Theme handled by column style
                connection["path"],  # Theme handled by column style
            )

        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text("UNIX Domain Sockets"),
                style=get_theme().info,
            )
        )
