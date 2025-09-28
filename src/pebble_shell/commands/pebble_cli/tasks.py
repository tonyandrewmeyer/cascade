"""Implementation of TasksCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops
from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag, validate_min_args
from ...utils.table_builder import create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class TasksCommand(Command):
    """List tasks for a change."""

    name = "pebble-tasks"
    help = "List tasks for a specific change"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the tasks command."""
        if handle_help_flag(self, args):
            return 0

        if validate_min_args(self.shell, args, 1, "tasks <change-id>"):
            return 1

        change_id = ops.pebble.ChangeID(args[0])
        change = client.get_change(change_id)  # type: ignore
        assert isinstance(change, ops.pebble.Change)

        if not change.tasks:
            self.console.print(f"No tasks found for change {change_id}")
            return 0

        self._show_tasks_table(change)
        return 0

    def _show_tasks_table(self, change: ops.pebble.Change):
        """Display tasks in a Rich table."""
        table = create_standard_table()
        table.status_column("Kind")
        table.status_column("Status")
        table.data_column("Summary")
        table.secondary_column("Progress")
        table.secondary_column("Log")

        for task in change.tasks:
            kind = str(task.kind) if task.kind else "unknown"
            status = str(task.status) if task.status else "unknown"
            summary = str(task.summary) if task.summary else ""
            progress = (
                str(task.progress)
                if hasattr(task, "progress") and task.progress
                else ""
            )
            log = str(task.log) if hasattr(task, "log") and task.log else ""

            table.add_row(kind, status, summary, progress, log)

        self.console.print(
            Panel(
                table,
                title=get_theme().highlight_text(f"Tasks for Change {change.id}"),
                style=get_theme().info,
            )
        )
