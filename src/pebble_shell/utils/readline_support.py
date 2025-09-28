"""Readline support for expected shell experience."""

from __future__ import annotations

import glob
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..commands import AliasCommand, Command
    from ..shell import PebbleShell

from .enhanced_completer import EnhancedCompleter

import readline


class ReadlineWrapper:
    """Wrapper for readline functionality with fallback."""

    def __init__(self):
        self.has_readline = readline is not None
        self.completer_function: Callable[..., Any] | None = None

        if not self.has_readline:
            return
        assert readline is not None

        readline.parse_and_bind("tab: complete")

        # Enable history search with arrow keys.
        readline.parse_and_bind('"\\e[A": history-search-backward')
        readline.parse_and_bind('"\\e[B": history-search-forward')

        readline.set_history_length(1000)

    def set_completer(self, completer: Callable[..., str | None]) -> None:
        """Set tab completion function."""
        if not self.has_readline:
            return
        assert readline is not None

        self.completer_function = completer
        readline.set_completer(completer)

    def add_history(self, line: str) -> None:
        """Add line to readline history."""
        if not self.has_readline or not line.strip():
            return
        assert readline is not None

        readline.add_history(line.strip())

    def clear_history(self) -> None:
        """Clear readline history."""
        if not self.has_readline:
            return
        assert readline is not None

        readline.clear_history()

    def get_history_length(self) -> int:
        """Get current history length."""
        if not self.has_readline:
            return 0
        assert readline is not None

        return readline.get_current_history_length()

    def get_history_item(self, index: int) -> str | None:
        """Get history item by index."""
        if not self.has_readline:
            return None
        assert readline is not None

        try:
            return readline.get_history_item(index + 1)  # readline is 1-indexed
        except (IndexError, ValueError):
            return None

    def input_with_prompt(self, prompt: str) -> str:
        """Get input with prompt and history support."""
        if self.has_readline:
            return input(prompt)
        return input(prompt)


class ShellCompleter:
    """Tab completion for shell commands."""

    def __init__(self, commands: dict[str, Command], alias_command: AliasCommand):
        self.commands = commands
        self.alias_command = alias_command
        self.command_names = [*list(commands.keys()), "help", "exit", "clear"]

    def complete(self, text: str, state: int) -> str | None:
        """Tab completion function for readline.

        Args:
            text: Text to complete
            state: Completion state

        Returns:
            Completion suggestion or None
        """
        assert readline is not None
        try:
            if state == 0:
                # First call, generate completion list.
                line = readline.get_line_buffer()
                parts = line.lstrip().split()

                if not parts or (len(parts) == 1 and not line.endswith(" ")):
                    self.matches = self._complete_command(text)
                else:
                    self.matches = self._complete_path(text)

            if state < len(self.matches):
                return self.matches[state]
            return None

        except Exception:
            return None

    def _complete_command(self, text: str) -> list[str]:
        """Complete command names."""
        matches = [cmd for cmd in self.command_names if cmd.startswith(text)]
        matches.extend(
            alias for alias in self.alias_command.aliases if alias.startswith(text)
        )

        return sorted(matches)

    def _complete_path(self, text: str) -> list[str]:
        """Complete file paths."""
        # Simple path completion - in a real implementation,
        # this would use the Pebble client to list directories
        try:
            if not text:
                text = "./*"
            elif not text.endswith("*"):
                if text.endswith("/"):
                    text += "*"
                else:
                    text += "*"

            matches = glob.glob(text)

            # Add trailing slash for directories
            result: list[str] = []
            for match in matches:
                if os.path.isdir(match):
                    result.append(match + "/")
                else:
                    result.append(match)

            return result

        except Exception:
            return []


def setup_readline_support(
    commands: dict[str, Command], alias_command: AliasCommand, shell: PebbleShell
) -> ReadlineWrapper:
    """Set up readline support for the shell.

    Args:
        commands: Available shell commands
        alias_command: Alias command instance
        shell: Shell instance for enhanced completion

    Returns:
        ReadlineWrapper instance
    """
    wrapper = ReadlineWrapper()

    if wrapper.has_readline:
        completer = EnhancedCompleter(shell, commands, alias_command)
        wrapper.set_completer(completer.complete)
        print("Enhanced readline support enabled (use tab for smart completion)")
    else:
        print(
            "Readline not available (install 'readline' package for an enhanced experience)"
        )

    return wrapper
