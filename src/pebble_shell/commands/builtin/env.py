"""Implementation of EnvCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops
from rich.panel import Panel
from rich.table import Table

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, read_proc_environ
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class EnvCommand(Command):
    """Command for displaying environment variables from process files."""
    name = "env"
    help = "Show environment variables"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the env command to display environment variables."""
        if handle_help_flag(self, args):
            return 0
        console = self.console
        pids = ["self", "1"]  # Try self first, then init

        for pid in pids:
            try:
                env_vars = read_proc_environ(client, pid)

                table = Table(
                    show_header=True,
                    header_style="bold magenta",
                    box=None,
                    expand=False,
                )
                table.add_column("Variable", style="cyan", no_wrap=True)
                table.add_column("Value", style="green")

                for name, value in env_vars.items():
                    table.add_row(name, value)

                if table.row_count > 0:
                    console.print(
                        Panel(
                            table,
                            title=f"[b]Environment Variables from /proc/{pid}/environ[/b]",
                            style="cyan",
                        )
                    )
                    return 0
            except ProcReadError:  # noqa: PERF203
                # Continue to next PID if this one fails
                continue

        console.print(
            Panel(
                "Could not read environment variables from any source",
                title="[b red]env Error[/b red]",
                style="red",
            )
        )
        return 1
