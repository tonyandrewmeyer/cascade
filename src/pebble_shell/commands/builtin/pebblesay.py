"""Implementation of PebblesayCommand."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Union

import ops
from rich.text import Text

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    from collections.abc import Callable

    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: This isn't as pretty as I'd like. Maybe the "pebbles in a stream" idea is
# a bad one, and we should think of something else?


class PebblesayCommand(Command):
    """Command for displaying ASCII art with speech bubbles."""
    name = "pebblesay"
    help = "Display ASCII art with a speech bubble. Usage: pebblesay MESSAGE"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the pebblesay command to display ASCII art with messages."""
        if handle_help_flag(self, args):
            return 0
        console = self.console
        message = " ".join(args) if args else "Cascade!"

        # Create a beautiful speech bubble
        bubble_lines = self._create_speech_bubble(message)

        # Create enhanced pebble art
        art = self._create_pebble_art()

        # Print the speech bubble and art
        for line in bubble_lines:
            console.print(Text(line, style="bold cyan"))
        console.print(art)
        return 0

    def _create_speech_bubble(self, message: str) -> list[str]:
        # Wrap message to fit nicely
        max_width = 50
        words = message.split()
        lines: list[str] = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line += (word + " ") if current_line else word
            else:
                if current_line:
                    lines.append(current_line.rstrip())
                current_line = word
        if current_line:
            lines.append(current_line.rstrip())

        if not lines:
            lines = [""]

        # Find the longest line for bubble width
        max_line_length = max(len(line) for line in lines)
        bubble_width = max(max_line_length + 4, 20)  # Minimum width

        # Create bubble lines
        bubble_lines: list[str] = []

        # Top border with rounded corners
        top_border = " " + "─" * (bubble_width - 2)
        bubble_lines.append(f"  ╭{top_border}╮")

        # Message lines with proper padding
        for line in lines:
            padding = " " * (bubble_width - len(line) - 2)
            bubble_lines.append(f"  │ {line}{padding} │")

        # Bottom border with tail
        bottom_border = " " + "─" * (bubble_width - 2)
        bubble_lines.append(f"  ╰{bottom_border}╯")
        bubble_lines.append("      ▼")

        return bubble_lines

    def _create_pebble_art(self) -> Text:
        art = Text()
        width = 80
        height = 25

        # Define pebble characters with different styles
        pebble_chars = [
            ("●", "bold white"),
            ("○", "bold yellow"),
            ("◉", "bold magenta"),
            ("◐", "bold green"),
            ("◑", "bold red"),
            ("◒", "bold blue"),
            ("◓", "bold cyan"),
            ("◎", "white"),
            ("◈", "yellow"),
            ("◆", "magenta"),
            ("◇", "green"),
            ("◊", "red"),
            ("◈", "blue"),
            ("◈", "cyan"),
        ]

        # Water characters with wave effects
        water_chars = [
            ("~", "bright_blue"),
            ("≈", "cyan"),
            ("∽", "blue"),
            ("~", "bold blue"),
            ("∿", "bold cyan"),
            (" ", "bright_blue"),
        ]

        # Create wave patterns
        wave_patterns: list[Callable[[int, int], bool]] = [
            lambda row, col: (row + col) % 8 == 0,  # type: ignore
            lambda row, col: (row - col) % 11 == 0,  # type: ignore
            lambda row, col: (row * 2 + col) % 13 == 0,  # type: ignore
            lambda row, col: (row + col * 2) % 7 == 0,  # type: ignore
        ]

        for row in range(height):
            line = Text()
            for col in range(width):
                # Create pebble placement with better distribution
                pebble_probability = self._get_pebble_probability(
                    row, col, height, width
                )

                if random.random() < pebble_probability:  # noqa: S311
                    char, style = random.choice(pebble_chars)  # noqa: S311
                    line.append(char, style=style)
                else:
                    # Create water with wave effects
                    is_wave = any(pattern(row, col) for pattern in wave_patterns)
                    if is_wave:
                        char, style = random.choice(water_chars[:3])  # noqa: S311
                    else:
                        char, style = random.choice(  # noqa: S311
                            water_chars[3:]
                        )  # Use space-like chars
                    line.append(char, style=style)

            art.append(line)
            art.append("\n")

        return art

    def _get_pebble_probability(
        self, row: int, col: int, height: int, width: int
    ) -> float:
        # Create a more natural distribution
        center_x, center_y = width // 2, height // 2

        # Distance from center (normalized)
        dx = abs(col - center_x) / (width // 2)
        dy = abs(row - center_y) / (height // 2)
        distance = (dx * dx + dy * dy) ** 0.5

        # Base probability decreases with distance from center
        base_prob = 0.15 * (1 - distance * 0.7)

        # Add some randomness and clustering
        if row > height * 0.6:  # More pebbles in lower area
            base_prob *= 1.5

        # Add some horizontal clustering
        if col % 3 == 0:
            base_prob *= 1.2

        # Add some vertical clustering
        if row % 4 == 0:
            base_prob *= 1.1

        return min(base_prob, 0.4)  # Cap at 40%
