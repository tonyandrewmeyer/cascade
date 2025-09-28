"""Implementation of UlimitCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError, parse_proc_limits_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UlimitCommand(Command):
    """Command for displaying system resource limits."""
    name = "ulimit"
    help = "Show resource limits"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the ulimit command to show resource limits."""
        if handle_help_flag(self, args):
            return 0

        console = self.console
        show_all = False
        option = None

        if args:
            if args[0] == "-a":
                show_all = True
            elif args[0].startswith("-"):
                option = args[0][1:]
            else:
                console.print(
                    Panel(
                        "Usage: ulimit [-a] [-option]\n"
                        "  -a: show all limits\n"
                        "  Options: c, d, f, l, m, n, s, t, u, v",
                        title="[b]ulimit[/b]",
                        style="cyan",
                    )
                )
                return 1

        try:
            limits = parse_proc_limits_file(client, "self")
        except ProcReadError as e:
            console.print(
                Panel(
                    f"Could not read limits: {e}",
                    title="[b red]ulimit Error[/b red]",
                    style="red",
                )
            )
            return 1

        if not limits:
            console.print(
                Panel(
                    "No limit information available",
                    title="[b red]ulimit Error[/b red]",
                    style="red",
                )
            )
            return 1

        if show_all or not option:
            table = Table(
                show_header=True,
                header_style="bold magenta",
                title="[b]Resource Limits[/b]",
                title_style="bold cyan",
                box=None,
                expand=False,
            )
            table.add_column("Resource", style="cyan", no_wrap=True)
            table.add_column("Soft Limit", style="green", justify="right")
            table.add_column("Hard Limit", style="yellow", justify="right")
            table.add_column("Units", style="white", no_wrap=True)

            for name, data in limits.items():
                soft = (
                    "[bold green]unlimited[/bold green]"
                    if data["soft"] == "unlimited"
                    else data["soft"]
                )
                hard = (
                    "[bold yellow]unlimited[/bold yellow]"
                    if data["hard"] == "unlimited"
                    else data["hard"]
                )
                table.add_row(name, soft, hard, data["units"])

            console.print(table)
            return 0

        # Show specific limit (simplified mapping)
        limit_map = {
            "c": "Max core file size",
            "d": "Max data size",
            "f": "Max file size",
            "l": "Max locked memory",
            "m": "Max memory size",
            "n": "Max file descriptors",
            "s": "Max stack size",
            "t": "Max cpu time",
            "u": "Max user processes",
            "v": "Max virtual memory",
        }

        target = limit_map.get(option)
        if target:
            for name, data in limits.items():
                if target.lower() in name.lower():
                    soft = (
                        "[bold green]unlimited[/bold green]"
                        if data["soft"] == "unlimited"
                        else data["soft"]
                    )
                    console.print(
                        Panel(
                            Text(f"Limit: {soft}", style="bold cyan"),
                            title=f"[b]ulimit -{option}[/b]",
                            style="cyan",
                        )
                    )
                    return 0

        console.print(
            Panel(
                f"Unknown option: {option}",
                title="[b red]ulimit Error[/b red]",
                style="red",
            )
        )
        return 1
