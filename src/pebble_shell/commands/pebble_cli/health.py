"""Implementation of HealthCommand."""

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


class HealthCommand(Command):
    """Show overall health status."""

    name = "health"
    help = "Show overall health status of all checks"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the health command."""
        if handle_help_flag(self, args):
            return 0

        check_infos = client.get_checks()
        plan = client.get_plan()
        checks = plan.checks

        if not checks:
            self.console.print("No health checks configured")
            return 0

        self._show_health_table(check_infos, checks)
        return 0

    def _show_health_table(
        self,
        check_infos: list[ops.pebble.CheckInfo],
        checks: dict[str, ops.pebble.Check],
    ):
        """Display health status in a Rich table."""
        healthy_count = sum(
            1 for check_info in check_infos if check_info.status == "up"
        )
        unhealthy_count = len(check_infos) - healthy_count

        table = create_standard_table()
        table.primary_id_column("Name")
        table.status_column("Status")
        table.status_column("Level")
        table.status_column("Type")
        table.data_column("Target")

        for check_info in check_infos:
            check = checks[check_info.name]
            name = str(check.name)
            status = str(check_info.status) if check_info.status else "unknown"
            level = str(check_info.level) if check_info.level else ""
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

            table.add_row(name, status, level, check_type, target)

        if unhealthy_count == 0:
            summary_text = get_theme().success_text("✓ All checks are healthy")
        else:
            summary_text = get_theme().error_text(
                f"⚠ {unhealthy_count} checks are unhealthy"
            )

        summary_panel = Panel(
            f"Health Status: {healthy_count}/{len(checks)} checks healthy\n{summary_text}",
            title=get_theme().highlight_text("Health Summary"),
            style=get_theme().info,
        )

        self.console.print(summary_panel)
        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Health Checks"),
                style=get_theme().info,
            )
        )
