"""Implementation of SyslogCommand."""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

import ops
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: The syslog can be very large, and Pebble can only get the whole file.
# Can we do anything about that?


class SyslogCommand(Command):
    """Show syslog information from /var/log/syslog or similar files."""

    name = "syslog"
    help = "Show syslog information. Use -n NUM for last NUM lines, -f to follow, and an optional pattern to filter."
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute syslog command."""
        if handle_help_flag(self, args):
            return 0
        num_lines = 100
        follow = False
        pattern = None
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "-n" and i + 1 < len(args):
                try:
                    num_lines = int(args[i + 1])
                except ValueError:
                    self.console.print("[red]Invalid number for -n[/red]")
                    return 1
                i += 1
            elif arg == "-f":
                follow = True
            elif not arg.startswith("-") and pattern is None:
                pattern = arg
            i += 1

        log_files = [
            "/var/log/syslog",
            "/var/log/messages",
            "/var/log/system.log",
            "/var/log/user.log",
        ]
        log_file = None
        content = ""
        for lf in log_files:
            try:
                with client.pull(lf) as file:
                    content = file.read()
                assert isinstance(content, str)
            except ops.pebble.PathError:
                continue
            log_file = lf
            break
        else:
            self.console.print(
                Panel(
                    Text(
                        "No syslog file found. Tried: " + ", ".join(log_files),
                        style="yellow",
                    ),
                    title="[b]syslog[/b]",
                    style="bold magenta",
                )
            )
            return 1
        lines = content.splitlines()
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            lines = [line for line in lines if regex.search(line)]
        if num_lines > 0:
            lines = lines[-num_lines:]
        self._print_syslog_lines(lines)
        if follow:
            self._follow_syslog(client, log_file, pattern, num_lines)
        return 0

    def _print_syslog_lines(self, lines: list[str]):
        for line in lines:
            style = self._get_line_style(line)
            self.console.print(Text(line, style=style))

    def _get_line_style(self, line: str) -> str:
        if any(word in line.lower() for word in ["error", "fail", "critical"]):
            return "bold red"
        if any(word in line.lower() for word in ["warn", "deprecated"]):
            return "yellow"
        if any(word in line.lower() for word in ["info", "started", "listening"]):
            return "green"
        if any(word in line.lower() for word in ["debug"]):
            return "cyan"
        return "white"

    def _follow_syslog(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        log_file: str,
        pattern: str | None,
        num_lines: int,
    ):
        regex = re.compile(pattern, re.IGNORECASE) if pattern else None
        with Live(refresh_per_second=2, screen=False) as live:
            pos = 0
            while True:
                try:
                    with client.pull(log_file) as file:
                        content = file.read()
                    assert isinstance(content, str)
                    lines = content.splitlines()
                    if regex:
                        lines = [line for line in lines if regex.search(line)]
                    if num_lines > 0:
                        lines = lines[-num_lines:]
                    new_lines = lines[pos:]
                    if new_lines:
                        for line in new_lines:
                            style = self._get_line_style(line)
                            live.console.print(Text(line, style=style))
                        pos = len(lines)
                    time.sleep(1)
                except KeyboardInterrupt:  # noqa: PERF203
                    break
