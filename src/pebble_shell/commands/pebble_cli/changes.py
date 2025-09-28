"""Implementation of ChangesCommand."""

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


class ChangesCommand(Command):
    """List changes."""

    name = "pebble-changes"
    help = "List recent changes"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the changes command."""
        if handle_help_flag(self, args):
            return 0

        changes = client.get_changes()

        if not changes:
            self.console.print("No changes found")
            return 0

        self._show_changes_table(changes)
        return 0

    def _show_changes_table(self, changes: list[ops.pebble.Change]):
        """Display changes in a Rich table."""
        table = create_standard_table()
        table.primary_id_column("ID")
        table.status_column("Kind")
        table.status_column("Status")
        table.data_column("Summary")
        table.secondary_column("Tasks")

        for change in changes:
            change_id = str(change.id)
            kind = str(change.kind) if change.kind else "unknown"
            status = str(change.status) if change.status else "unknown"
            summary = str(change.summary) if change.summary else ""
            tasks = str(len(change.tasks)) if change.tasks else "0"

            table.add_row(change_id, kind, status, summary, tasks)

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text("Changes"),
                style=get_theme().info,
            )
        )
