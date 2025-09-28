"""Implementation of NoticeCommand."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import ops
from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag, validate_min_args
from ...utils.table_builder import create_details_table, create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class NoticeCommand(Command):
    """Get details of a specific notice."""

    name = "pebble-notice"
    help = "Get details of a specific notice"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the notice command."""
        if handle_help_flag(self, args):
            return 0

        if validate_min_args(self.shell, args, 1, "notice <notice-id>"):
            return 1

        notice_id = args[0]
        try:
            notice = client.get_notice(notice_id)
        except ops.pebble.APIError:
            self.console.print(f"Notice {notice_id} not found")
            return 1

        self._show_notice_details(notice)
        return 0

    def _show_notice_details(self, notice: ops.pebble.Notice):
        """Display notice details in a Rich table."""
        table = create_details_table()

        table.add_row("Notice ID", str(notice.id))
        table.add_row("Type", str(notice.type) if notice.type else "unknown")
        table.add_row("Key", str(notice.key) if notice.key else "")

        if notice.first_occurred:
            table.add_row(
                "First Occurred", notice.first_occurred.strftime("%Y-%m-%d %H:%M:%S")
            )
        if notice.last_occurred:
            table.add_row(
                "Last Occurred", notice.last_occurred.strftime("%Y-%m-%d %H:%M:%S")
            )
        if notice.last_repeated:
            table.add_row(
                "Last Repeated", notice.last_repeated.strftime("%Y-%m-%d %H:%M:%S")
            )

        if notice.occurrences:
            table.add_row("Occurrences", str(notice.occurrences))
        if notice.repeat_after:
            table.add_row("Repeat After", str(notice.repeat_after))

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Notice Details"),
                style=get_theme().info,
            )
        )

        if notice.last_data:
            data_table = create_standard_table()
            data_table.primary_id_column("Key")
            data_table.data_column("Value")

            for key, value in notice.last_data.items():
                if isinstance(value, dict | list):
                    data_table.add_row(key, json.dumps(value, indent=2))
                else:
                    data_table.add_row(key, str(value))

            self.console.print(
                Panel(
                    data_table,
                    title=get_theme().highlight_text("Notice Data"),
                    style=get_theme().success,
                )
            )
