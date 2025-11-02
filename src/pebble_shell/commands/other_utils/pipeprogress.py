"""Implementation of PipeProgressCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the builtin category?
class PipeProgressCommand(Command):
    """Implementation of pipe_progress command."""

    name = "pipe_progress"
    help = "Show progress for data through a pipe"
    category = "Utilities"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the pipe_progress command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        result = parse_flags(
            args,
            {
                "s": str,  # size
                "t": str,  # title
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        expected_size = flags.get("s")
        title = flags.get("t") or "Progress"

        try:
            # TODO: Implement real pipe progress

            self.console.print(f"[bold]{title}[/bold]")

            if expected_size:
                try:
                    size_bytes = int(expected_size)
                    size_mb = size_bytes / (1024 * 1024)
                    self.console.print(f"Expected size: {size_mb:.1f}MB")
                except ValueError:
                    self.console.print(f"Expected size: {expected_size}")

            # Simulate progress (in a real implementation, this would read/write data)
            progress_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]

            for i in range(10):
                char = progress_chars[i % len(progress_chars)]
                percent = (i + 1) * 10
                self.console.print(f"\r{char} {percent}% complete", end="")
                time.sleep(0.1)

            self.console.print("\n[green]✓ Complete[/green]")
            return 0

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Progress interrupted[/yellow]")
            return 1
        except Exception as e:
            self.console.print(f"[red]pipe_progress: {e}[/red]")
            return 1
