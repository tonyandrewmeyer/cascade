"""Waitfor command for Cascade.

This module provides implementation for the waitfor command that waits
for a process to exit on the remote system.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from ...utils.proc_reader import ProcReadError, read_proc_cmdline, read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class WaitforCommand(Command):
    """Wait for a process to exit."""

    name = "waitfor"
    help = "Wait for a process to exit"
    category = "System"

    def show_help(self):
        """Show command help."""
        help_text = """Wait for a process to exit.

Usage: waitfor [OPTIONS] PID

Options:
    -h, --help          Show this help message
    -t, --timeout SECS  Maximum time to wait (default: no limit)
    -i, --interval SECS Polling interval in seconds (default: 0.5)
    -q, --quiet         Don't show waiting message
    -v, --verbose       Show periodic status updates

Arguments:
    PID                 Process ID to wait for

Polls the remote /proc filesystem to detect when the process exits.

Examples:
    waitfor 1234              # Wait for PID 1234 to exit
    waitfor -t 60 1234        # Wait up to 60 seconds
    waitfor -v 1234           # Show status updates while waiting
    waitfor -q 1234           # Wait silently
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the waitfor command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "t": int,
                "timeout": int,
                "i": str,  # Use str to allow float values
                "interval": str,
                "q": bool,
                "quiet": bool,
                "v": bool,
                "verbose": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if not positional_args:
            self.console.print("[red]waitfor: missing PID argument[/red]")
            self.console.print("Usage: waitfor <pid>")
            return 1

        try:
            pid = int(positional_args[0])
        except ValueError:
            self.console.print(
                f"[red]waitfor: invalid PID: {positional_args[0]}[/red]"
            )
            return 1

        timeout = flags["t"] or flags["timeout"]
        interval_str = flags["i"] or flags["interval"]
        quiet = flags["q"] or flags["quiet"]
        verbose = flags["v"] or flags["verbose"]

        # Parse interval (default 0.5 seconds)
        try:
            interval = float(interval_str) if interval_str else 0.5
        except ValueError:
            self.console.print(f"[red]waitfor: invalid interval: {interval_str}[/red]")
            return 1

        if interval <= 0:
            self.console.print("[red]waitfor: interval must be positive[/red]")
            return 1

        # Check if process exists initially
        if not self._process_exists(client, pid):
            if not quiet:
                self.console.print(
                    f"[yellow]waitfor: process {pid} does not exist[/yellow]"
                )
            return 1

        # Get process name for display
        proc_name = self._get_process_name(client, pid)

        if not quiet:
            if proc_name:
                self.console.print(
                    f"[cyan]Waiting for process {pid} ({proc_name}) to exit...[/cyan]"
                )
            else:
                self.console.print(
                    f"[cyan]Waiting for process {pid} to exit...[/cyan]"
                )

        # Wait for process to exit
        start_time = time.time()
        last_status_time = start_time

        try:
            while self._process_exists(client, pid):
                elapsed = time.time() - start_time

                # Check timeout
                if timeout and elapsed >= timeout:
                    if not quiet:
                        self.console.print(
                            f"[yellow]waitfor: timeout after {timeout} seconds[/yellow]"
                        )
                    return 124  # Standard timeout exit code

                # Show periodic status in verbose mode
                if verbose and (time.time() - last_status_time) >= 5:
                    self.console.print(
                        f"[dim]Still waiting... ({int(elapsed)}s elapsed)[/dim]"
                    )
                    last_status_time = time.time()

                time.sleep(interval)

        except KeyboardInterrupt:
            if not quiet:
                self.console.print("\n[yellow]waitfor: interrupted[/yellow]")
            return 130  # Standard interrupt exit code

        # Process exited
        elapsed = time.time() - start_time
        if not quiet:
            self.console.print(
                f"[green]Process {pid} exited after {elapsed:.1f}s[/green]"
            )

        return 0

    def _process_exists(self, client: ClientType, pid: int) -> bool:
        """Check if a process exists by checking /proc/<pid>."""
        try:
            # Try to list /proc/<pid> - if it exists, process is running
            client.list_files(f"/proc/{pid}")
            return True
        except ops.pebble.PathError:
            return False

    def _get_process_name(self, client: ClientType, pid: int) -> str | None:
        """Get the process name/command for display."""
        try:
            cmdline = read_proc_cmdline(client, str(pid))
            if cmdline and cmdline != "unknown":
                # Truncate long command lines
                if len(cmdline) > 40:
                    return cmdline[:37] + "..."
                return cmdline
        except ProcReadError:
            pass

        try:
            comm = read_proc_file(client, f"/proc/{pid}/comm")
            return comm.strip()
        except ProcReadError:
            pass

        return None
