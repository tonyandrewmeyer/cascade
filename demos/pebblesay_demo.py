#!/usr/bin/env python3
"""Demo script for the improved pebblesay command.

Shows various messages with the enhanced ASCII art.
"""

import os
import sys

# Add the src directory to the path so we can import pebble_shell
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rich.console import Console

from pebble_shell.commands.builtin import PebblesayCommand


def demo_pebblesay():
    """Demo the improved pebblesay command."""
    console = Console()

    class MockShell:
        def __init__(self):
            self.console = console

    shell = MockShell()
    command = PebblesayCommand(shell)  # type: ignore

    messages = [
        "Hello from Cascade!",
        "This is a much better pebblesay command with improved ASCII art and beautiful speech bubbles.",
        "Short message",
        "A very long message that will wrap to multiple lines and demonstrate the text wrapping capabilities of the improved speech bubble system",
        "🎉 Celebrating the new pebblesay! 🎉",
        "Debugging containers has never been more fun!",
    ]

    console.print("\n[bold cyan]Improved Pebblesay Demo[/bold cyan]\n")

    for i, message in enumerate(messages, 1):
        console.print(f"\n[bold yellow]Demo {i}:[/bold yellow] {message}")
        console.print("-" * 80)

        try:
            command.execute(None, message.split())  # type: ignore
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        console.print("-" * 80)

    console.print("\n[bold green]Demo complete![/bold green]")


if __name__ == "__main__":
    demo_pebblesay()
