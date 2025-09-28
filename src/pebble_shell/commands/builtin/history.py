"""Implementation of HistoryCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

import ops
from rich.panel import Panel
from rich.table import Table

from ...utils.command_helpers import handle_help_flag
from ...utils.history import get_shell_history
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class HistoryCommand(Command):
    """Command for managing and displaying shell command history."""
    name = "history"
    help = "Show command history (supports !!, !n, !string, ^old^new)"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the history command to show or manage command history."""
        history = get_shell_history()
        console = self.console

        if handle_help_flag(self, args):
            return 0

        if not args:
            # Show all history with line numbers
            self._show_history(history.get_history())
            return 0

        if args[0] == "-c":
            history.clear_history()
            console.print(Panel("History cleared", style="bold green"))
            return 0

        if args[0] == "-s":
            self._show_stats(history.get_stats())
            return 0

        if args[0].startswith("-"):
            console.print(
                Panel(
                    style="bold yellow",
                )
            )
            return 0

        try:
            count = int(args[0])
            self._show_history(history.get_history(count))
            return 0
        except ValueError:
            pass

        # Try as search pattern.
        pattern = args[0]
        matches = history.search_history(pattern)
        if matches:
            console.print(
                Panel(
                    f"History entries matching '[cyan]{pattern}[/cyan]':",
                    style="bold blue",
                )
            )
            self._show_history(matches)
            return 0

        console.print(
            Panel(
                f"No history entries found matching '[red]{pattern}[/red]'",
                style="bold red",
            )
        )
        return 1

    def _show_history(self, commands: list[str]) -> None:
        console = self.console
        if not commands:
            console.print(Panel("No history entries", style="bold yellow"))
            return

        total_history = get_shell_history().get_history()
        start_num = len(total_history) - len(commands) + 1

        table = Table(
            show_header=True, header_style="bold magenta", box=None, expand=False
        )
        table.add_column("#", style="cyan", no_wrap=True)
        table.add_column("Command", style="green")
        for i, command in enumerate(commands, start=start_num):
            table.add_row(str(i), command)
        console.print(table)

    def _show_stats(self, stats: dict[str, Any]) -> None:
        console = self.console
        lines = [
            f"[b]Total commands:[/b] {stats['total_commands']}",
            f"[b]Unique commands:[/b] {stats['unique_commands']}",
        ]
        if stats["most_used"]:
            cmd, count = stats["most_used"]
            lines.append(
                f"[b]Most used command:[/b] [cyan]{cmd}[/cyan] ({count} times)"
            )
        lines.append(f"[b]History file:[/b] {stats['history_file']}")
        console.print(
            Panel("\n".join(lines), title="History Statistics", style="bold blue")
        )
