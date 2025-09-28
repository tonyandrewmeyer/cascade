"""Show socket statistics."""

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


class SocketStatsCommand(Command):
    """Show socket statistics."""

    name = "ss"
    help = "Show socket statistics"
    category = "Network Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute ss-like command."""
        if handle_help_flag(self, args):
            return 0

        stats: dict[str, dict[str, int]] = {}

        # Count TCP sockets by state.
        try:
            tcp_connections = parse_proc_net_connections(client, "tcp")
            tcp_states: dict[str, int] = {}
            for connection in tcp_connections:
                if "state" in connection:
                    state_name = connection["state"]
                    tcp_states[state_name] = tcp_states.get(state_name, 0) + 1
            stats["tcp"] = tcp_states
        except ProcReadError:
            stats["tcp"] = {}

        # Count UDP sockets.
        try:
            udp_connections = parse_proc_net_connections(client, "udp")
            stats["udp"] = {"total": len(udp_connections)}
        except ProcReadError:
            stats["udp"] = {"total": 0}

        # Count UNIX sockets.
        try:
            unix_connections = parse_proc_net_connections(client, "unix")
            stats["unix"] = {"total": len(unix_connections)}
        except ProcReadError:
            stats["unix"] = {"total": 0}

        table = create_standard_table()
        table.status_column("Type")
        table.status_column("State")
        table.numeric_column("Count")

        if stats.get("tcp"):
            for state_name, count in stats["tcp"].items():
                table.add_row(
                    "TCP",  # Theme handled by column style
                    state_name,  # Theme handled by column style
                    str(count),  # Theme handled by column style
                )
        if stats.get("udp"):
            table.add_row(
                "UDP", "-", str(stats["udp"]["total"])
            )  # Theme handled by column style
        if stats.get("unix"):
            table.add_row(
                "UNIX", "-", str(stats["unix"]["total"])
            )  # Theme handled by column style

        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text("Socket Statistics"),
                style=get_theme().info,
            )
        )
        return 0
