"""Show network interfaces and statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ...utils import format_bytes
from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import parse_proc_net_dev
from ...utils.table_builder import create_standard_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class NetworkCommand(Command):
    """Show network interfaces and statistics."""

    name = "net"
    help = "Show network interface statistics"
    category = "Network Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute netstat-like command."""
        if handle_help_flag(self, args):
            return 0

        interfaces = parse_proc_net_dev(client)

        table = create_standard_table()
        table.primary_id_column("Interface")
        table.numeric_column("RX Bytes")
        table.secondary_column("RX Packets")
        table.numeric_column("TX Bytes")
        table.secondary_column("TX Packets")

        for interface_data in interfaces:
            rx_bytes = interface_data["rx_bytes"]
            tx_bytes = interface_data["tx_bytes"]
            assert isinstance(rx_bytes, int), (
                f"rx_bytes should be int, got {type(rx_bytes)}"
            )
            assert isinstance(tx_bytes, int), (
                f"tx_bytes should be int, got {type(tx_bytes)}"
            )

            table.add_row(
                interface_data["interface"],  # Theme handled by column style
                format_bytes(rx_bytes),  # Theme handled by column style
                str(interface_data["rx_packets"]),
                format_bytes(tx_bytes),  # Theme handled by column style
                str(interface_data["tx_packets"]),
            )

        self.shell.console.print(table.build())
        return 0
