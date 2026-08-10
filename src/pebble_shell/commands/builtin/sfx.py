"""Sound effects command for Cascade.

This module provides implementation for the sfx command that plays
sound files from the local ~/.cascade/sounds/ directory.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


def get_sounds_dir() -> Path:
    """Get the path to the sounds directory."""
    return Path.home() / ".cascade" / "sounds"


def get_audio_player() -> tuple[str, list[str]] | None:
    """Find an available audio player command.

    Returns:
        Tuple of (command_name, extra_args) or None if no player found.
    """
    system = platform.system()

    if system == "Darwin":
        # macOS
        if shutil.which("afplay"):
            return ("afplay", [])
    elif system == "Linux":
        # Linux - try various players
        if shutil.which("paplay"):
            return ("paplay", [])
        if shutil.which("aplay"):
            return ("aplay", ["-q"])  # quiet mode
        if shutil.which("play"):  # sox
            return ("play", ["-q"])
    elif system == "Windows" and shutil.which("powershell"):
        # Windows - PowerShell can play sounds
        return ("powershell", ["-c", "(New-Object Media.SoundPlayer"])

    return None


class SfxCommand(Command):
    """Play sound effects."""

    name = "sfx"
    help = "Play sound effects from ~/.cascade/sounds/"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        sounds_dir = get_sounds_dir()
        help_text = f"""Play sound effects.

Usage: sfx [OPTIONS] [SOUND_NAME]

Options:
    -h, --help      Show this help message
    -l, --list      List available sounds
    -p, --path      Show sounds directory path

Arguments:
    SOUND_NAME      Name of sound to play (without extension)
                    If omitted, lists available sounds

Sound files should be placed in:
    {sounds_dir}/

Supported formats depend on your system's audio player:
    macOS: .aiff, .mp3, .wav, .m4a (via afplay)
    Linux: .wav, .ogg (via paplay/aplay)

Examples:
    sfx success       # Play success.wav (or .mp3, etc.)
    sfx -l            # List available sounds
    sfx               # Same as -l
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the sfx command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "l": bool,
                "list": bool,
                "p": bool,
                "path": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        sounds_dir = get_sounds_dir()

        if flags["p"] or flags["path"]:
            self.console.print(str(sounds_dir))
            return 0

        # Ensure sounds directory exists
        if not sounds_dir.exists():
            sounds_dir.mkdir(parents=True, exist_ok=True)
            self.console.print(
                f"[yellow]Created sounds directory: {sounds_dir}[/yellow]"
            )
            self.console.print("[dim]Add sound files (.wav, .mp3, etc.) to this directory[/dim]")
            return 0

        # List sounds if no argument or -l flag
        if flags["l"] or flags["list"] or not positional_args:
            return self._list_sounds(sounds_dir)

        sound_name = positional_args[0]
        return self._play_sound(sounds_dir, sound_name)

    def _list_sounds(self, sounds_dir: Path) -> int:
        """List available sounds."""
        # Common audio extensions
        audio_extensions = {".wav", ".mp3", ".ogg", ".aiff", ".m4a", ".flac"}

        sounds = [
            file.stem
            for file in sounds_dir.iterdir()
            if file.is_file() and file.suffix.lower() in audio_extensions
        ]

        if not sounds:
            self.console.print(f"[yellow]No sounds found in {sounds_dir}[/yellow]")
            self.console.print("[dim]Add .wav, .mp3, or other audio files to this directory[/dim]")
            return 0

        self.console.print(f"[bold]Available sounds in {sounds_dir}:[/bold]")
        for sound in sorted(sounds):
            self.console.print(f"  {sound}")

        return 0

    def _play_sound(self, sounds_dir: Path, sound_name: str) -> int:
        """Play a sound file."""
        # Find the sound file (try various extensions)
        audio_extensions = [".wav", ".mp3", ".ogg", ".aiff", ".m4a", ".flac"]

        sound_file = None
        for ext in audio_extensions:
            candidate = sounds_dir / f"{sound_name}{ext}"
            if candidate.exists():
                sound_file = candidate
                break

        if sound_file is None:
            # Maybe they specified the full filename
            candidate = sounds_dir / sound_name
            if candidate.exists():
                sound_file = candidate

        if sound_file is None:
            self.console.print(f"[red]sfx: sound not found: {sound_name}[/red]")
            self.console.print(f"[dim]Looking in: {sounds_dir}[/dim]")
            return 1

        # Find audio player
        player = get_audio_player()
        if player is None:
            self.console.print("[red]sfx: no audio player found[/red]")
            self.console.print("[dim]Install afplay (macOS), paplay/aplay (Linux), or sox[/dim]")
            return 1

        player_cmd, extra_args = player

        # Build command
        if player_cmd == "powershell":
            # Windows needs special handling
            cmd = [
                "powershell", "-c",
                f"(New-Object Media.SoundPlayer '{sound_file}').PlaySync()"
            ]
        else:
            cmd = [player_cmd, *extra_args, str(sound_file)]

        try:
            # S603: Command is built from known audio players and user's own sound files
            subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603
            return 0
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]sfx: failed to play sound: {e}[/red]")
            return 1
        except FileNotFoundError:
            self.console.print(f"[red]sfx: audio player not found: {player_cmd}[/red]")
            return 1
