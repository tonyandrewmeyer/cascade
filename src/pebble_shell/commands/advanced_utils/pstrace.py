"""Implementation of PstraceCommand."""

from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.proc_reader import (
    ProcReadError,
    read_proc_file,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PstraceCommand(Command):
    """Implementation of pstrace command (process trace viewer)."""

    name = "pstrace"
    help = "Simple process tracing via /proc filesystem"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Simple process tracing via /proc filesystem.

Usage: pstrace [OPTIONS] PID

Description:
    Monitor process activity by reading /proc filesystem.
    This is a read-only implementation using available proc data.

Options:
    -f              Follow child processes
    -o FILE         Output to file
    -p PID          Attach to process PID
    -c              Count system calls (estimate)
    -t              Show timestamps
    -h, --help      Show this help message

Examples:
    pstrace 1234
    pstrace -t -o trace.log 5678
    pstrace -c 9012
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the pstrace command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "f": bool,  # follow children
                "o": str,  # output file
                "p": int,  # pid
                "c": bool,  # count syscalls
                "t": bool,  # timestamps
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        follow_children = flags.get("f", False)
        output_file = flags.get("o")
        pid = flags.get("p")
        count_syscalls = flags.get("c", False)
        show_timestamps = flags.get("t", False)

        # Get PID from arguments or flag
        if pid is None:
            if not positional_args:
                self.console.print("[red]pstrace: missing PID[/red]")
                return 1
            try:
                pid = int(positional_args[0])
            except ValueError:
                self.console.print(
                    f"[red]pstrace: invalid PID '{positional_args[0]}'[/red]"
                )
                return 1

        try:
            # Check if process exists
            try:
                read_proc_file(client, f"/proc/{pid}/stat")  # Check if process exists
            except ProcReadError:
                self.console.print(f"[red]pstrace: process {pid} not found[/red]")
                return 1

            # Start monitoring
            self._monitor_process(
                client,
                pid,
                follow_children,
                output_file,
                count_syscalls,
                show_timestamps,
            )
            return 0

        except KeyboardInterrupt:
            self.console.print("\n[yellow]pstrace: interrupted[/yellow]")
            return 0
        except Exception as e:
            self.console.print(f"[red]pstrace: {e}[/red]")
            return 1

    def _monitor_process(
        self,
        client: ClientType,
        pid: int,
        follow_children: bool,
        output_file: str,
        count_syscalls: bool,
        show_timestamps: bool,
    ):
        """Monitor a process by reading /proc data."""
        output_lines = []
        syscall_counts = {}

        self.console.print(f"[green]Monitoring process {pid}...[/green]")

        try:
            while True:
                timestamp = time.time() if show_timestamps else None

                # Read process status
                try:
                    stat_content = read_proc_file(client, f"/proc/{pid}/stat")
                    stat_data = stat_content.strip().split()

                    # Read process status details
                    status_data = read_proc_file(client, f"/proc/{pid}/status")

                    # Parse basic info
                    if len(stat_data) >= 3:
                        comm = stat_data[1].strip("()")
                        state = stat_data[2]

                        # Create trace line
                        trace_line = f"PID {pid} ({comm}) state={state}"

                        if show_timestamps:
                            trace_line = f"[{timestamp:.6f}] {trace_line}"

                        # Look for syscall info in status
                        for line in status_data.splitlines():
                            if line.startswith("syscall:"):
                                syscall_info = line.split(":", 1)[1].strip()
                                trace_line += f" syscall={syscall_info}"

                                if count_syscalls:
                                    syscall_counts[syscall_info] = (
                                        syscall_counts.get(syscall_info, 0) + 1
                                    )

                        output_lines.append(trace_line)

                        if not output_file:
                            self.console.print(trace_line)

                    # Follow children if requested
                    if follow_children:
                        with contextlib.suppress(ProcReadError):
                            # This would list threads/children
                            read_proc_file(client, f"/proc/{pid}/task")

                except ops.pebble.PathError:
                    self.console.print(f"[yellow]Process {pid} terminated[/yellow]")
                    break

                time.sleep(0.1)  # Polling interval

        except KeyboardInterrupt:
            pass

        # Write output file if specified
        if output_file:
            try:
                content = "\n".join(output_lines) + "\n"
                with client.push(output_file, encoding="utf-8") as f:
                    f.write(content)
                self.console.print(f"[green]Trace written to {output_file}[/green]")
            except Exception as e:
                self.console.print(f"[red]Failed to write output file: {e}[/red]")

        # Show syscall counts if requested
        if count_syscalls and syscall_counts:
            self.console.print("\n[bold]System call counts:[/bold]")
            for syscall, count in sorted(syscall_counts.items()):
                self.console.print(f"  {syscall}: {count}")
