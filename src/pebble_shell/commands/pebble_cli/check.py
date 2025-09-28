"""Implementation of CheckCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag, validate_min_args
from ...utils.table_builder import create_details_table, create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class CheckCommand(Command):
    """Get details of a specific health check."""

    name = "pebble-check"
    help = "Get details of a specific health check"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the check command."""
        if handle_help_flag(self, args):
            return 0

        if validate_min_args(self.shell, args, 1, "check <check-name>"):
            return 1

        check_name = args[0]
        checks = client.get_checks(names=[check_name])

        if not checks:
            self.console.print(f"Check '{check_name}' not found")
            return 1

        check_info = checks[0]
        plan = client.get_plan()
        check = plan.checks[check_name]
        self._show_check_details(check_info, check)
        return 0

    def _show_check_details(
        self, check_info: ops.pebble.CheckInfo, check: ops.pebble.Check
    ):
        """Display check details in a Rich table."""
        table = create_details_table()

        table.add_row("Check Name", str(check.name))
        table.add_row(
            "Status", str(check_info.status) if check_info.status else "unknown"
        )
        table.add_row("Level", str(check_info.level) if check_info.level else "")
        table.add_row(
            "Failures", str(check_info.failures) if check_info.failures else "0"
        )

        if check_info.threshold:
            table.add_row("Threshold", str(check_info.threshold))
        if check_info.change_id:
            table.add_row("Change ID", str(check_info.change_id))

        check_type = ""
        target = ""
        period = ""
        period = str(check.period)

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

        if check_type:
            table.add_row("Type", check_type)
        if target:
            table.add_row("Target", target)
        if period:
            table.add_row("Period", period)

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Check Details"),
                style=get_theme().info,
            )
        )

        if check.http:
            self._show_http_config(check.http)
        elif check.tcp:
            self._show_tcp_config(check.tcp)
        elif check.exec:
            self._show_exec_config(check.exec)

    def _show_http_config(self, http_config: ops.pebble.HttpDict):
        """Display HTTP check configuration."""
        table = create_standard_table()
        table.secondary_column("Setting")
        table.data_column("Value")

        for key, value in http_config.items():
            table.add_row(key, str(value))

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("HTTP Configuration"),
                style=get_theme().success,
            )
        )

    def _show_tcp_config(self, tcp_config: ops.pebble.TcpDict):
        """Display TCP check configuration."""
        table = create_standard_table()
        table.secondary_column("Setting")
        table.data_column("Value")

        for key, value in tcp_config.items():
            table.add_row(key, str(value))

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("TCP Configuration"),
                style=get_theme().success,
            )
        )

    def _show_exec_config(self, exec_config: ops.pebble.ExecDict):
        """Display Exec check configuration."""
        table = create_standard_table()
        table.secondary_column("Setting")
        table.data_column("Value")

        for key, value in exec_config.items():
            table.add_row(key, str(value))

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Exec Configuration"),
                style=get_theme().success,
            )
        )
