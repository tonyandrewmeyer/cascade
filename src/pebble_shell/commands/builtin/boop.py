"""Boop command for Cascade.

This module provides implementation for the boop command that plays
success/failure sounds for command feedback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command
from .sfx import get_audio_player, get_sounds_dir

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class BoopCommand(Command):
    """Play success/failure sounds."""

    name = "boop"
    help = "Play success/failure feedback sounds"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        sounds_dir = get_sounds_dir()
        help_text = f"""Play success/failure feedback sounds.

Usage: boop [OPTIONS] [TYPE]
       command && boop || boop fail

Options:
    -h, --help      Show this help message

Arguments:
    TYPE            Sound type: success (default), fail, or error

Plays sounds from {sounds_dir}/:
    success.wav (or .mp3, etc.) - for success
    fail.wav or error.wav       - for failure

Falls back to terminal bell if no sound files are found.

Examples:
    boop                    # Play success sound
    boop success            # Same as above
    boop fail               # Play failure sound
    make && boop || boop fail   # Sound feedback for build
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the boop command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        # Determine sound type
        sound_type = "success"
        if positional_args:
            arg = positional_args[0].lower()
            if arg in ("fail", "failure", "error"):
                sound_type = "fail"
            elif arg in ("success", "ok", "done"):
                sound_type = "success"
            else:
                self.console.print(f"[yellow]boop: unknown type '{arg}', using success[/yellow]")

        # Try to play sound file
        if self._play_sound(sound_type):
            return 0

        # Fall back to terminal bell
        if sound_type == "fail":
            # Double beep for failure
            print("\a\a", end="", flush=True)
        else:
            print("\a", end="", flush=True)

        return 0

    def _play_sound(self, sound_type: str) -> bool:
        """Try to play a sound file. Returns True if successful."""
        import subprocess

        sounds_dir = get_sounds_dir()
        if not sounds_dir.exists():
            return False

        # Look for sound files
        audio_extensions = [".wav", ".mp3", ".ogg", ".aiff", ".m4a"]

        # For fail, also check "error"
        names_to_try = [sound_type]
        if sound_type == "fail":
            names_to_try.append("error")

        sound_file = None
        for name in names_to_try:
            for ext in audio_extensions:
                candidate = sounds_dir / f"{name}{ext}"
                if candidate.exists():
                    sound_file = candidate
                    break
            if sound_file:
                break

        if not sound_file:
            return False

        # Get audio player
        player = get_audio_player()
        if not player:
            return False

        player_cmd, extra_args = player

        try:
            cmd = [player_cmd, *extra_args, str(sound_file)]
            # S603: Command is built from known audio players and user's own sound files
            subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
