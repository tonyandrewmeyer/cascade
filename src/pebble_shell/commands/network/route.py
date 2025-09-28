"""Show routing table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
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
    """Show routing table."""

    name = "route"
    help = "Show routing table"
    category = "Network Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute route command."""
        if handle_help_flag(self, args):
            return 0

        routes = parse_proc_route(client)

        table = create_standard_table()
        table.primary_id_column("Destination")
        table.primary_id_column("Gateway")
        table.secondary_column("Genmask")
        table.status_column("Flags")
        table.secondary_column("Metric")
        table.data_column("Iface", no_wrap=True)

        for route in routes:
            table.add_row(
                route["destination"],  # Theme handled by column style
                route["gateway"],  # Theme handled by column style
                route["mask"],  # Theme handled by column style
                route["flags"],  # Theme handled by column style
                route["metric"],  # Theme handled by column style
                route["interface"],  # Theme handled by column style
            )

        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text("Kernel IP Routing Table"),
                style=get_theme().info,
            )
        )
        return 0
