"""Scriptreplay command for Cascade.

This module provides implementation for terminal session replay
command that works with the Pebble filesystem API.

The scriptreplay command simulates the functionality of the traditional Unix scriptreplay utility
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


class ScriptreplayCommand(Command):
    """Implementation of scriptreplay command."""

    name = "scriptreplay"
    help = "Replay recorded terminal sessions"
    category = "Terminal"

    def show_help(self):
        """Show command help."""
        help_text = """Replay recorded terminal sessions.

Usage: scriptreplay [OPTIONS] TIMINGFILE [TYPESCRIPT [DIVISOR]]

Description:
    Replay terminal sessions recorded with script command using
    timing information to reproduce original timing.

Options:
    -t, --timing TIMINGFILE     Timing file (default: timing)
    -s, --typescript TYPESCRIPT Output file (default: typescript)
    -d, --divisor DIVISOR       Speed up replay by dividing delays
    -m, --maxdelay SECONDS      Maximum delay between outputs
    --timing-format FORMAT      Timing format: classic or advanced
    -h, --help                  Show this help message

Examples:
    scriptreplay timing typescript          # Basic replay
    scriptreplay -d 2 timing typescript     # 2x speed
    scriptreplay -m 1.0 timing typescript   # Max 1 second delays
    scriptreplay --timing-format advanced timing.json typescript
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the scriptreplay command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "t": str,  # timing file
                "timing": str,  # timing file
                "s": str,  # typescript file
                "typescript": str,  # typescript file
                "d": float,  # divisor
                "divisor": float,  # divisor
                "m": float,  # max delay
                "maxdelay": float,  # max delay
                "timing-format": str,  # timing format
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        # Determine files from arguments and flags
        if positional_args:
            timing_file = positional_args[0]
            typescript_file = (
                positional_args[1] if len(positional_args) > 1 else "typescript"
            )
            divisor = float(positional_args[2]) if len(positional_args) > 2 else 1.0
        else:
            timing_file = flags.get("t") or flags.get("timing", "timing")
            typescript_file = flags.get("s") or flags.get("typescript", "typescript")
            divisor = flags.get("d") or flags.get("divisor", 1.0)

        max_delay = flags.get("m") or flags.get("maxdelay")
        timing_format = flags.get("timing-format", "classic")

        if not timing_file:
            self.console.print("[red]scriptreplay: missing timing file[/red]")
            return 1

        try:
            return self._replay_session(
                client, timing_file, typescript_file, divisor, max_delay, timing_format
            )

        except Exception as e:
            self.console.print(f"[red]scriptreplay: {e}[/red]")
            return 1

    def _replay_session(
        self,
        client: ClientType,
        timing_file: str,
        typescript_file: str,
        divisor: float,
        max_delay: float | None,
        timing_format: str,
    ) -> int:
        """Replay a recorded session."""
        # Read timing file
        timing_content = safe_read_file(client, timing_file)
        if timing_content is None:
            self.console.print(
                f"[red]scriptreplay: cannot read timing file '{timing_file}'[/red]"
            )
            return 1

        # Read typescript file
        typescript_content = safe_read_file(client, typescript_file)
        if typescript_content is None:
            self.console.print(
                f"[red]scriptreplay: cannot read typescript file '{typescript_file}'[/red]"
            )
            return 1

        # Parse timing data
        try:
            timing_events = self._parse_timing_data(timing_content, timing_format)
        except Exception as e:
            self.console.print(
                f"[red]scriptreplay: error parsing timing file: {e}[/red]"
            )
            return 1

        # Parse typescript content
        try:
            session_chunks = self._parse_typescript_data(
                typescript_content, timing_events
            )
        except Exception as e:
            self.console.print(
                f"[red]scriptreplay: error parsing typescript file: {e}[/red]"
            )
            return 1

        # Start replay
        self.console.print(f"[green]Replaying session from {typescript_file}[/green]")
        self.console.print(f"[dim]Using timing from {timing_file}[/dim]")

        if divisor != 1.0:
            self.console.print(f"[dim]Speed: {divisor}x faster[/dim]")
        if max_delay:
            self.console.print(f"[dim]Max delay: {max_delay} seconds[/dim]")

        self.console.print("[dim]--- Session replay starts ---[/dim]")

        # Replay with timing
        try:
            for i, (delay, chunk) in enumerate(session_chunks):
                if i > 0:  # Don't delay before first chunk
                    actual_delay = delay / divisor
                    if max_delay and actual_delay > max_delay:
                        actual_delay = max_delay

                    if actual_delay > 0.01:  # Only sleep for significant delays
                        time.sleep(actual_delay)

                # Print chunk without newline to preserve formatting
                self.console.print(chunk, end="")

            self.console.print("\n[dim]--- Session replay complete ---[/dim]")
            return 0

        except KeyboardInterrupt:
            self.console.print("\n[yellow]scriptreplay: replay interrupted[/yellow]")
            return 130

    def _parse_timing_data(self, content: str, timing_format: str) -> list:
        """Parse timing data from file content."""
        if timing_format == "advanced":
            # Try to parse as JSON
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "events" in data:
                    return data["events"]
                else:
                    # Fall back to treating as list
                    return data if isinstance(data, list) else []
            except json.JSONDecodeError as err:
                raise ScriptError(
                    "Invalid JSON format in advanced timing file"
                ) from err
        else:
            # Classic format: timestamp size per line
            events = []
            for line_num, line in enumerate(content.strip().split("\n"), 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 2:
                    raise ScriptError(f"Invalid timing format at line {line_num}")

                try:
                    timestamp = float(parts[0])
                    size = int(parts[1])
                    events.append(
                        {
                            "timestamp": timestamp,
                            "size": size,
                            "type": "output",  # Classic format assumes output
                        }
                    )
                except ValueError as err:
                    raise ScriptError(
                        f"Invalid timing values at line {line_num}"
                    ) from err

            return events

    def _parse_typescript_data(self, content: str, timing_events: list) -> list:
        """Parse typescript content into chunks based on timing events."""
        chunks = []
        content_pos = 0

        # Skip header line if present
        if content.startswith("Script started on"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content_pos = first_newline + 1

        last_timestamp = 0.0

        for event in timing_events:
            if event.get("type") == "input":
                # Skip input events for replay (we only show output)
                continue

            size = event.get("size", 0)
            timestamp = event.get("timestamp", 0.0)

            # Calculate delay since last event
            delay = timestamp - last_timestamp
            last_timestamp = timestamp

            # Extract chunk of specified size
            if content_pos + size <= len(content):
                chunk = content[content_pos : content_pos + size]
                content_pos += size
            else:
                # Take remaining content if size is larger than available
                chunk = content[content_pos:]
                content_pos = len(content)

            # Skip footer line if present
            if chunk.startswith("Script done on"):
                break

            chunks.append((delay, chunk))

            # Stop if we've consumed all content
            if content_pos >= len(content):
                break

        return chunks
