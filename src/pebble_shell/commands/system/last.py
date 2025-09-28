"""Implementation of LastCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops
from rich.panel import Panel
from rich.text import Text

from ...utils.command_helpers import handle_help_flag
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class LastCommand(Command):
    """Show last login information."""

    name = "last"
    help = "Show last login information"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute last command."""
        if handle_help_flag(self, args):
            return 0
        # Try different log files for login information
        log_files = [
            "/var/log/auth.log",
            "/var/log/secure",
            "/var/log/wtmp",
            "/var/log/btmp",
        ]

        login_entries: list[tuple[str, str]] = []

        for log_file in log_files:
            try:
                with client.pull(log_file) as file:
                    content = file.read()
                assert isinstance(content, str)
            except ops.pebble.PathError:
                continue

            # Use list.extend for better performance
            login_entries.extend(
                (log_file, line)
                for line in content.splitlines()
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "session opened",
                        "accepted",
                        "login",
                        "sshd",
                    ]
                )
            )

        if not login_entries:
            self.console.print(
                Panel(
                    Text("No login information found", style="yellow"),
                    title="[b]last[/b]",
                    style="bold magenta",
                )
            )
            return 1

        # Sort by most recent (simplified - just take last 50 entries)
        login_entries = login_entries[-50:]

        table = create_enhanced_table()
        table.add_column("User", style="cyan", no_wrap=True)
        table.add_column("TTY", style="green", no_wrap=True)
        table.add_column("From", style="yellow", no_wrap=True)
        table.add_column("Login Time", style="blue", no_wrap=True)
        table.add_column("Logout Time", style="magenta", no_wrap=True)
        table.add_column("Duration", style="white", no_wrap=True)

        for _log_file, line in login_entries:
            # Parse login line (simplified parsing)
            parts = line.split()
            if len(parts) >= 5:
                # Try to extract user, tty, from, and time
                user = "unknown"
                tty = "?"
                from_host = "?"
                login_time = "unknown"

                # Look for common patterns
                for i, part in enumerate(parts):
                    if part in ["session", "opened", "accepted", "login"]:
                        if i > 0:
                            user = parts[i - 1]
                        break

                # Extract timestamp (usually at the beginning)
                if len(parts) >= 3:
                    login_time = " ".join(parts[:3])

                table.add_row(user, tty, from_host, login_time, "-", "-")

        self.console.print(table.build())
        return 0
