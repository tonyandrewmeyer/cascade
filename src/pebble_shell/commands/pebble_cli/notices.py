"""Implementation of NoticesCommand."""

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


class NoticesCommand(Command):
    """List notices."""

    name = "notices"
    help = "List notices"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the notices command."""
        if handle_help_flag(self, args):
            return 0

        notices = client.get_notices()

        if not notices:
            self.console.print("No notices found")
            return 1

        self._show_notices_table(notices)
        return 0

    def _show_notices_table(self, notices: list[ops.pebble.Notice]):
        """Display notices in a Rich table."""
        table = create_standard_table()
        table.primary_id_column("ID")
        table.status_column("Type")
        table.data_column("Key")
        table.secondary_column("First Occurred")
        table.secondary_column("Repeat After")
        table.numeric_column("Occurrences")

        for notice in notices:
            notice_id = str(notice.id)
            notice_type = str(notice.type) if notice.type else "unknown"
            key = str(notice.key) if notice.key else ""
            first_occurred = (
                notice.first_occurred.strftime("%Y-%m-%d %H:%M:%S")
                if notice.first_occurred
                else ""
            )
            repeat_after = str(notice.repeat_after) if notice.repeat_after else ""
            occurrences = str(notice.occurrences) if notice.occurrences else ""

            table.add_row(
                notice_id, notice_type, key, first_occurred, repeat_after, occurrences
            )

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Notices"),
                style=get_theme().info,
            )
        )
