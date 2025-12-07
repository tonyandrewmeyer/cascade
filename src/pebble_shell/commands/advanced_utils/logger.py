"""Implementation of LoggerCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LoggerCommand(Command):
    """Implementation of logger command."""

    name = "logger"
    help = "Write messages to the system log"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Write messages to the system log.

Usage: logger [OPTIONS] [MESSAGE]

Description:
    Send messages to the system logger (syslog).
    If no message is provided, read from standard input.

Options:
    -p PRIORITY     Set priority (facility.level)
    -t TAG          Add tag to message
    -i              Include process ID
    -s              Also write to stderr
    -f FILE         Read message from file
    -h, --help      Show this help message

Priority levels:
    emerg, alert, crit, err, warning, notice, info, debug

Facilities:
    kern, user, mail, daemon, auth, syslog, lpr, news,
    uucp, cron, authpriv, ftp, local0-local7

Examples:
    logger "System started"
    logger -p user.warning "Low disk space"
    logger -t myapp -i "Application started"
    echo "test" | logger
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the logger command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "p": str,  # priority
                "t": str,  # tag
                "i": bool,  # include PID
                "s": bool,  # stderr
                "f": str,  # file
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        flags.get(
            "p", "user.notice"
        )  # priority - not implemented in this simple version
        tag = flags.get("t") or "logger"
        include_pid = flags.get("i", False)
        also_stderr = flags.get("s", False)
        message_file = flags.get("f")

        try:
            # Get message
            if message_file:
                message_content = safe_read_file(client, message_file)
                message = message_content.strip() if message_content else ""
            elif positional_args:
                message = " ".join(positional_args)
            else:
                # Read from stdin (simulated)
                self.console.print(
                    "[yellow]logger: enter message (Ctrl+D to end):[/yellow]"
                )
                try:
                    message = input()
                except (EOFError, KeyboardInterrupt):
                    return 1

            if not message:
                self.console.print("[red]logger: no message to log[/red]")
                return 1

            # Format log entry
            pid_str = f"[{1234}]" if include_pid else ""  # Simulated PID
            log_entry = f"{tag}{pid_str}: {message}"

            # Write to syslog (simulated by writing to a log file)
            try:
                # Try to append to syslog
                log_path = "/var/log/messages"
                timestamp = time.strftime("%b %d %H:%M:%S")
                full_entry = f"{timestamp} hostname {log_entry}\n"

                try:
                    # Read existing log
                    existing_log = safe_read_file(client, log_path) or ""

                    # Append new entry
                    with client.push(log_path, encoding="utf-8") as f:
                        f.write(existing_log + full_entry)

                    self.console.print(f"[green]Logged: {log_entry}[/green]")

                except Exception:
                    # Fallback: just display the message
                    self.console.print(
                        f"[yellow]Would log to syslog: {log_entry}[/yellow]"
                    )

                # Also write to stderr if requested
                if also_stderr:
                    self.console.print(log_entry, file=self.error_console.file)

            except Exception:
                # Handle any errors in the logging process
                self.console.print(f"[yellow]Would log to syslog: {log_entry}[/yellow]")
                if also_stderr:
                    self.console.print(log_entry, file=self.error_console.file)

            return 0

        except Exception as e:
            self.console.print(f"[red]logger: {e}[/red]")
            return 1
