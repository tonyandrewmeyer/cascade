"""Pastas command for Cascade.

This module provides implementation for the pastas command that monitors
the clipboard and prints changes.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.clipboard import (
    ClipboardAccessError,
    ClipboardUnavailableError,
    paste_from_clipboard,
)
from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PastasCommand(Command):
    """Monitor the clipboard and print changes."""

    name = "pastas"
    help = "Monitor the clipboard and print changes"
    category = "Clipboard"

    def show_help(self):
        """Show command help."""
        help_text = """Monitor the clipboard and print changes.

Usage: pastas [OPTIONS]

Options:
    -h, --help          Show this help message
    -t, --timeout SECS  Watch for SECS seconds (default: 30, max: 300)
    -i, --interval MS   Check interval in milliseconds (default: 500)
    -q, --quiet         Don't print initial clipboard content

Monitors the local clipboard and prints whenever the content changes.
Press Ctrl+C to stop monitoring.

Examples:
    pastas              # Monitor for 30 seconds
    pastas -t 60        # Monitor for 60 seconds
    pastas -i 100       # Check every 100ms
    pastas -q           # Don't show initial content
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the pastas command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "t": int,
                "timeout": int,
                "i": int,
                "interval": int,
                "q": bool,
                "quiet": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        timeout = flags["t"] or flags["timeout"] or 30
        interval_ms = flags["i"] or flags["interval"] or 500
        quiet = flags["q"] or flags["quiet"]

        # Cap timeout at 5 minutes
        if timeout > 300:
            self.console.print("[yellow]pastas: timeout capped at 300 seconds[/yellow]")
            timeout = 300

        # Convert interval to seconds
        interval = interval_ms / 1000.0

        try:
            # Get initial clipboard content
            last_content = paste_from_clipboard()

            if not quiet:
                self.console.print("[dim]Current clipboard:[/dim]")
                preview = self._format_preview(last_content)
                self.console.print(preview)
                self.console.print()

            self.console.print(
                f"[dim]Monitoring clipboard for {timeout}s (Ctrl+C to stop)...[/dim]"
            )

            start_time = time.time()
            change_count = 0

            while time.time() - start_time < timeout:
                try:
                    current_content = paste_from_clipboard()

                    if current_content != last_content:
                        change_count += 1
                        elapsed = time.time() - start_time
                        self.console.print(
                            f"\n[green]Change #{change_count}[/green] "
                            f"[dim](at {elapsed:.1f}s)[/dim]"
                        )
                        preview = self._format_preview(current_content)
                        self.console.print(preview)
                        last_content = current_content

                    time.sleep(interval)

                except KeyboardInterrupt:
                    self.console.print("\n[dim]Stopped monitoring.[/dim]")
                    break

            if change_count == 0:
                self.console.print("[dim]No changes detected.[/dim]")
            else:
                self.console.print(f"\n[dim]Total changes: {change_count}[/dim]")

            return 0

        except ClipboardUnavailableError as e:
            self.console.print(f"[red]pastas: {e}[/red]")
            return 1
        except ClipboardAccessError as e:
            self.console.print(f"[red]pastas: {e}[/red]")
            return 1

    def _format_preview(self, text: str) -> str:
        """Format text for preview display."""
        if not text:
            return "[dim](empty)[/dim]"

        # Escape Rich markup
        text = text.replace("[", "\\[")

        # Truncate if too long
        lines = text.split("\n")
        if len(lines) > 5:
            preview_lines = lines[:5]
            preview_lines.append(f"... ({len(lines) - 5} more lines)")
            text = "\n".join(preview_lines)
        elif len(text) > 200:
            text = text[:200] + "..."

        return text
