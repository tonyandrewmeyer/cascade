"""Implementation of ServicesCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from ...utils.table_builder import create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class ServicesCommand(Command):
    """List services and their status."""

    name = "pebble-services"
    help = "List all services and their status"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the services command."""
        if handle_help_flag(self, args):
            return 0

        services = client.get_services()

        if not services:
            self.console.print("No services configured")
            return 0

        self._show_services_table(services)
        return 0

    def _show_services_table(self, services: list[ops.pebble.ServiceInfo]):
        """Display services in a Rich table."""
        table = create_standard_table()
        table.primary_id_column("Service")
        table.status_column("Startup")
        table.status_column("Current")
        table.status_column("Status")

        for service in services:
            service_name = str(service.name)
            startup = str(service.startup) if service.startup else "disabled"
            current = str(service.current) if service.current else "inactive"

            status = "running" if service.is_running() else "stopped"

            table.add_row(service_name, startup, current, status)

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Services"),
                style=get_theme().info,
            )
        )
