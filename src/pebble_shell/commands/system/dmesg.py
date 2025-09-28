"""Implementation of DmesgCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops
from rich.panel import Panel
from rich.text import Text

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class DmesgCommand(Command):
    """Show kernel ring buffer messages."""

    name = "dmesg"
    help = "Show kernel ring buffer messages"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute dmesg command."""
        if handle_help_flag(self, args):
            return 0
        # Try different sources for kernel messages
        sources = [
            "/proc/kmsg",
            "/var/log/dmesg",
            "/var/log/kern.log",
            "/var/log/messages",
        ]

        content = ""
        for source in sources:
            try:
                with client.pull(source) as file:
                    content = file.read()
                break
            except ops.pebble.PathError:
                continue

        if not content:
            self.console.print(
                Panel(
                    Text(
                        "No kernel messages found. Tried: " + ", ".join(sources),
                        style="yellow",
                    ),
                    title="[b]dmesg[/b]",
                    style="bold magenta",
                )
            )
            return 1

        # Parse and display messages
        assert isinstance(content, str)
        lines = content.splitlines()

        # Limit output if too many lines
        if len(lines) > 1000:
            lines = lines[-1000:]
            self.console.print("[yellow]Showing last 1000 lines...[/yellow]")

        for line in lines:
            if line.strip():
                # Color code different message types
                if "error" in line.lower() or "fail" in line.lower():
                    self.console.print(f"[red]{line}[/red]")
                elif "warning" in line.lower():
                    self.console.print(f"[yellow]{line}[/yellow]")
                elif "info" in line.lower():
                    self.console.print(f"[blue]{line}[/blue]")
                else:
                    self.console.print(line)

        return 0
