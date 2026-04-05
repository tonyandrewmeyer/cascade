"""Timer command for Cascade.

This module provides implementation for the timer command that provides
a countdown timer with audio alert.
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


def parse_duration(duration_str: str) -> int | None:
    """Parse a duration string into seconds.

    Supports formats like:
        30        -> 30 seconds
        30s       -> 30 seconds
        5m        -> 5 minutes (300 seconds)
        1h        -> 1 hour (3600 seconds)
        1h30m     -> 1 hour 30 minutes
        1:30      -> 1 minute 30 seconds
        1:30:00   -> 1 hour 30 minutes

    Returns None if parsing fails.
    """
    duration_str = duration_str.strip().lower()

    # Try MM:SS or HH:MM:SS format
    if ":" in duration_str:
        parts = duration_str.split(":")
        try:
            if len(parts) == 2:
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None

    # Try plain number (seconds)
    try:
        return int(duration_str)
    except ValueError:
        pass

    # Try duration with units (e.g., 1h30m15s)
    total_seconds = 0
    pattern = r"(\d+)\s*(h|m|s)?"
    matches = re.findall(pattern, duration_str)

    if not matches:
        return None

    for value, unit in matches:
        value = int(value)
        if unit == "h":
            total_seconds += value * 3600
        elif unit == "m":
            total_seconds += value * 60
        else:  # 's' or no unit
            total_seconds += value

    return total_seconds if total_seconds > 0 else None


def format_time(seconds: int) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


class TimerCommand(Command):
    """Countdown timer with audio alert."""

    name = "timer"
    help = "Countdown timer with audio alert"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Countdown timer with audio alert.

Usage: timer [OPTIONS] DURATION

Options:
    -h, --help      Show this help message
    -q, --quiet     Don't show countdown display
    -m, --message   Message to display when timer ends

Arguments:
    DURATION        Time to count down. Formats:
                    30      - 30 seconds
                    30s     - 30 seconds
                    5m      - 5 minutes
                    1h      - 1 hour
                    1h30m   - 1 hour 30 minutes
                    1:30    - 1 minute 30 seconds
                    1:30:00 - 1 hour 30 minutes

When the timer ends, plays a sound (if available) or beeps.

Examples:
    timer 5m              # 5 minute timer
    timer 1h30m           # 1.5 hour timer
    timer 2:30            # 2 minutes 30 seconds
    timer -m "Break!" 25m # Pomodoro timer with message
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the timer command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "q": bool,
                "quiet": bool,
                "m": str,
                "message": str,
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
            self.console.print("[red]timer: missing duration argument[/red]")
            self.console.print("Usage: timer <duration>")
            return 1

        duration = parse_duration(positional_args[0])
        if duration is None:
            self.console.print(
                f"[red]timer: invalid duration: {positional_args[0]}[/red]"
            )
            return 1

        if duration <= 0:
            self.console.print("[red]timer: duration must be positive[/red]")
            return 1

        quiet = flags["q"] or flags["quiet"]
        message = flags["m"] or flags["message"] or "Timer done!"

        return self._run_timer(duration, quiet, message)

    def _run_timer(self, duration: int, quiet: bool, message: str) -> int:
        """Run the countdown timer."""
        remaining = duration

        if not quiet:
            self.console.print(
                f"[cyan]Timer set for {format_time(duration)}[/cyan]"
            )
            self.console.print("[dim]Press Ctrl+C to cancel[/dim]\n")

        try:
            while remaining > 0:
                if not quiet:
                    # Use carriage return to update in place
                    print(f"\r  {format_time(remaining)}  ", end="", flush=True)

                time.sleep(1)
                remaining -= 1

            if not quiet:
                print("\r" + " " * 20 + "\r", end="")  # Clear the line

        except KeyboardInterrupt:
            if not quiet:
                print()
            self.console.print("[yellow]Timer cancelled[/yellow]")
            return 130

        # Timer finished - alert!
        self.console.print(f"[bold green]{message}[/bold green]")
        self._play_alert()

        return 0

    def _play_alert(self):
        """Play the timer alert sound."""
        # Try to play a sound file
        try:
            from .sfx import get_audio_player, get_sounds_dir

            # Check if we have a timer sound
            sounds_dir = get_sounds_dir()
            if sounds_dir.exists():
                import subprocess
                audio_extensions = [".wav", ".mp3", ".ogg", ".aiff", ".m4a"]
                for name in ["timer", "alarm", "alert", "done", "success"]:
                    for ext in audio_extensions:
                        sound_file = sounds_dir / f"{name}{ext}"
                        if sound_file.exists():
                            player = get_audio_player()
                            if player:
                                player_cmd, extra_args = player
                                cmd = [player_cmd, *extra_args, str(sound_file)]
                                try:
                                    # S603: Known audio player with user's sound file
                                    subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603
                                    return
                                except (subprocess.CalledProcessError, FileNotFoundError):
                                    pass
        except ImportError:
            pass

        # Fall back to multiple beeps
        for _ in range(3):
            print("\a", end="", flush=True)
            time.sleep(0.3)
