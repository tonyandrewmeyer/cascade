"""Implementation of ChecksCommand."""

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


class ChecksCommand(Command):
    """List health checks."""

    name = "pebble-checks"
    help = "List all health checks and their status"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the checks command."""
        if handle_help_flag(self, args):
            return 0

        check_infos = client.get_checks()
        plan = client.get_plan()
        checks = plan.checks

        if not checks:
            self.console.print("No health checks configured")
            return 0

        self._show_checks_table(check_infos, checks)
        return 0

    def _show_checks_table(
        self,
        check_infos: list[ops.pebble.CheckInfo],
        checks: dict[str, ops.pebble.Check],
    ):
        """Display checks in a Rich table."""
        table = create_standard_table()
        table.primary_id_column("Name")
        table.status_column("Level")
        table.status_column("Status")
        table.numeric_column("Failures")
        table.status_column("Type")
        table.data_column("Target")

        for check_info in check_infos:
            check = checks[check_info.name]
            name = str(check.name)
            level = str(check_info.level) if check_info.level else "unknown"
            status = str(check_info.status) if check_info.status else "unknown"
            failures = str(check_info.failures) if check_info.failures else "0"

            check_type = ""
            target = ""

            if check.http:
                check_type = "http"
                assert "url" in check.http
                target = check.http["url"]
            elif check.tcp:
                check_type = "tcp"
                assert "host" in check.tcp
                host = check.tcp["host"]
                assert "port" in check.tcp
                port = check.tcp["port"]
                target = f"{host}:{port}" if host else str(port)
            elif check.exec:
                check_type = "exec"
                assert "command" in check.exec
                target = check.exec["command"]

            table.add_row(name, level, status, failures, check_type, target)

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Health Checks"),
                style=get_theme().info,
            )
        )
