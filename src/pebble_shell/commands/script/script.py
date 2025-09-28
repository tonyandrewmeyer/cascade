"""Script command for Cascade.

This module provides implementation for terminal session recording
command that works with the Pebble filesystem API.

The script command simulates the functionality of the traditional Unix script utility
while working within the Cascade shell environment.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class ScriptError(Exception):
    """Exception raised for script command errors."""


class ScriptCommand(Command):
    """Implementation of script command."""

    name = "script"
    help = "Record terminal sessions to typescript files"
    category = "Terminal"

    def show_help(self):
        """Show command help."""
        help_text = """Record terminal sessions to typescript files.

Usage: script [OPTIONS] [FILE]

Description:
    Record terminal sessions including input and output with timing
    information. Creates typescript and timing files for later replay.

Options:
    -a, --append        Append to existing typescript file
    -c COMMAND          Run specific command instead of shell
    -e, --return        Return exit code of child process
    -f, --flush         Flush output after each write
    -o, --output-limit SIZE  Maximum output per session (bytes)
    -q, --quiet         Be quiet (don't print start/stop messages)
    -t TIMINGFILE       Write timing data to file (default: timing)
    --timing-format FORMAT  Timing format: classic or advanced
    -h, --help          Show this help message

Examples:
    script                      # Record to typescript
    script session.log          # Record to specific file
    script -c "ls -la"          # Record specific command
    script -t timing.log out.log # Custom timing and output files
    script -q session.txt       # Quiet mode
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the script command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "a": bool,  # append
                "append": bool,  # append
                "c": str,  # command
                "e": bool,  # return exit code
                "return": bool,  # return exit code
                "f": bool,  # flush
                "flush": bool,  # flush
                "o": int,  # output limit
                "output-limit": int,  # output limit
                "q": bool,  # quiet
                "quiet": bool,  # quiet
                "t": str,  # timing file
                "timing-format": str,  # timing format
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        # Determine output file
        output_file = positional_args[0] if positional_args else "typescript"

        append_mode = flags.get("a", False) or flags.get("append", False)
        command = flags.get("c")
        return_exit = flags.get("e", False) or flags.get("return", False)
        flush_output = flags.get("f", False) or flags.get("flush", False)
        output_limit = flags.get("o") or flags.get("output-limit")
        quiet = flags.get("q", False) or flags.get("quiet", False)
        timing_file = flags.get("t", "timing")
        timing_format = flags.get("timing-format", "classic")

        try:
            return self._start_recording(
                client,
                output_file,
                timing_file,
                append_mode,
                command,
                return_exit,
                flush_output,
                output_limit,
                quiet,
                timing_format,
            )

        except Exception as e:
            self.console.print(f"[red]script: {e}[/red]")
            return 1

    def _start_recording(
        self,
        client: ClientType,
        output_file: str,
        timing_file: str,
        append_mode: bool,
        command: str | None,
        return_exit: bool,
        flush_output: bool,
        output_limit: int | None,
        quiet: bool,
        timing_format: str,
    ) -> int:
        """Start recording a terminal session."""
        if not quiet:
            if command:
                self.console.print(f"Script started, command: {command}")
            else:
                self.console.print("Script started, recording to terminal")
            self.console.print(f"Output file is {output_file}")
            if timing_file:
                self.console.print(f"Timing file is {timing_file}")

        # Check if files exist for append mode
        if append_mode:
            existing_output = safe_read_file(client, output_file)
            existing_timing = (
                safe_read_file(client, timing_file) if timing_file else None
            )

            if existing_output is not None and not quiet:
                self.console.print(f"Appending to existing file {output_file}")
            if existing_timing is not None and timing_file and not quiet:
                self.console.print(f"Appending to existing timing file {timing_file}")

        # Simulate recording session
        start_time = time.time()
        session_data = []
        timing_data = []

        if command:
            # Record specific command execution
            exit_code = self._record_command(
                client,
                command,
                session_data,
                timing_data,
                start_time,
                output_limit,
                flush_output,
            )
        else:
            # Record interactive session simulation
            exit_code = self._record_interactive_session(
                client,
                session_data,
                timing_data,
                start_time,
                output_limit,
                flush_output,
                quiet,
            )

        # Generate output content
        session_output = self._format_session_output(session_data, start_time)

        # Generate timing content
        timing_output = ""
        if timing_file:
            timing_output = self._format_timing_output(
                timing_data, timing_format, start_time
            )

        # Show what would be written (since we're in read-only mode)
        mode = "append to" if append_mode else "write to"

        self.console.print(f"[yellow]script: would {mode} {output_file}:[/yellow]")
        if len(session_output) > 1000:
            self.console.print(f"[dim]{session_output[:500]}...[/dim]")
            self.console.print(
                f"[dim]...(truncated, total {len(session_output)} bytes)[/dim]"
            )
        else:
            self.console.print(f"[dim]{session_output}[/dim]")

        if timing_file:
            self.console.print(f"[yellow]script: would {mode} {timing_file}:[/yellow]")
            if len(timing_output) > 500:
                self.console.print(f"[dim]{timing_output[:200]}...[/dim]")
                self.console.print(
                    f"[dim]...(truncated, total {len(timing_output.splitlines())} lines)[/dim]"
                )
            else:
                self.console.print(f"[dim]{timing_output}[/dim]")

        if not quiet:
            self.console.print("Script done")
            if timing_file:
                self.console.print(f"Timing data saved to {timing_file}")

        return exit_code if return_exit else 0

    def _record_command(
        self,
        client: ClientType,
        command: str,
        session_data: list,
        timing_data: list,
        start_time: float,
        output_limit: int | None,
        flush_output: bool,
    ) -> int:
        """Record execution of a specific command."""
        current_time = time.time()

        # Record command input
        session_data.append(
            {"timestamp": current_time, "type": "input", "data": f"{command}\r\n"}
        )
        timing_data.append(
            {
                "timestamp": current_time - start_time,
                "type": "input",
                "size": len(command) + 2,
            }
        )

        # TODO: Finish the actual command execution.
        try:
            output = f"[Simulated output of command: {command}]\n"
            output += "This would be the actual command output in a real session.\n"

            current_time = time.time()
            session_data.append(
                {"timestamp": current_time, "type": "output", "data": output}
            )
            timing_data.append(
                {
                    "timestamp": current_time - start_time,
                    "type": "output",
                    "size": len(output),
                }
            )

            # Check output limit
            if output_limit and len(output) > output_limit:
                self.console.print(
                    f"[yellow]script: output limit of {output_limit} bytes exceeded[/yellow]"
                )
                return 1

            return 0

        except Exception:
            return 1

    def _record_interactive_session(
        self,
        client: ClientType,
        session_data: list,
        timing_data: list,
        start_time: float,
        output_limit: int | None,
        flush_output: bool,
        quiet: bool,
    ) -> int:
        """Record an interactive session simulation."""
        if not quiet:
            self.console.print(
                "[yellow]script: simulating interactive session[/yellow]"
            )
            self.console.print(
                "[dim]In a real implementation, this would start an interactive shell[/dim]"
            )
        # TODO: Finish this implementation.
        return 0

    def _format_session_output(self, session_data: list, start_time: float) -> str:
        """Format session data into typescript format."""
        output_lines = []
        output_lines.append(f"Script started on {time.ctime(start_time)}")

        output_lines.extend(entry["data"] for entry in session_data)

        output_lines.append(f"Script done on {time.ctime()}")
        return "".join(output_lines)

    def _format_timing_output(
        self, timing_data: list, timing_format: str, start_time: float
    ) -> str:
        """Format timing data."""
        if timing_format == "advanced":
            # Advanced format with JSON
            return json.dumps(
                {"version": 2, "start_time": start_time, "events": timing_data},
                indent=2,
            )
        else:
            # Classic format: timestamp size
            lines = []
            for entry in timing_data:
                timestamp = entry["timestamp"]
                size = entry["size"]
                lines.append(f"{timestamp:.6f} {size}")
            return "\n".join(lines) + "\n"
