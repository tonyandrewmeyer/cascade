"""Show ARP table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
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
    help = "Show ARP table"
    category = "Network"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute arp command."""
        if handle_help_flag(self, args):
            return 0

        arp_entries = parse_proc_arp(client)

        table = create_standard_table()
        table.primary_id_column("IP address")
        table.secondary_column("HW type")
        table.status_column("Flags")
        table.data_column("HW address", no_wrap=True)
        table.secondary_column("Mask")
        table.primary_id_column("Device")

        for entry in arp_entries:
            table.add_row(
                entry["ip_address"],  # Theme handled by column style
                entry["hw_type"],  # Theme handled by column style
                entry["flags"],  # Theme handled by column style
                entry["hw_address"],  # Theme handled by column style
                entry["mask"],  # Theme handled by column style
                entry["device"],  # Theme handled by column style
            )

        self.shell.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text("ARP Table"),
                style=get_theme().info,
            )
        )
        return 0
