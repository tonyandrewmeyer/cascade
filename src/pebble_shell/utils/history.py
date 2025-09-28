"""Shell history management for Cascade."""

from __future__ import annotations

import logging
import os
import tempfile


class ShellHistory:
    """Manages shell command history."""

    def __init__(self, max_size: int = 1000, history_file: str | None = None):
        self.max_size = max_size
        self.history: list[str] = []
        self.current_index = 0

        if history_file:
            self.history_file = history_file
        else:
            # TODO: Use a more appropriate default path.
            self.history_file = os.path.join(tempfile.gettempdir(), ".cascade_history")

        self._load_history()

    def add_command(self, command: str) -> None:
        """Add a command to history.

        Args:
            command: Command to add to history
        """
        command = command.strip()
        if not command:
            return
        if self.history and self.history[-1] == command:
            return
        if command.startswith("history"):
            return
        self.history.append(command)
        if len(self.history) > self.max_size:
            self.history = self.history[-self.max_size :]
        self.current_index = len(self.history)
        self._save_history()

    def get_previous(self) -> str | None:
        """Get previous command in history.

        Returns:
            Previous command or None if at beginning
        """
        if not self.history or self.current_index <= 0:
            return None
        self.current_index -= 1
        return self.history[self.current_index]

    def get_next(self) -> str | None:
        """Get next command in history.

        Returns:
            Next command or None if at end
        """
        if not self.history or self.current_index >= len(self.history) - 1:
            self.current_index = len(self.history)
            return None
        self.current_index += 1
        return self.history[self.current_index]

    def get_history(self, count: int | None = None) -> list[str]:
        """Get history entries.

        Args:
            count: Number of entries to return (None for all)

        Returns:
            List of history entries
        """
        if count is None:
            return self.history.copy()
        if count <= 0:
            return []
        return self.history[-count:]

    def search_history(self, pattern: str) -> list[str]:
        """Search history for commands containing pattern.

        Args:
            pattern: Pattern to search for

        Returns:
            List of matching commands
        """
        return [cmd for cmd in self.history if pattern.lower() in cmd.lower()]

    def clear_history(self):
        """Clear all history."""
        self.history.clear()
        self.current_index = 0
        self._save_history()

    def _load_history(self):
        """Load history from file."""
        try:
            if not os.path.exists(self.history_file):
                return
            with open(self.history_file) as f:
                lines = f.readlines()
                self.history = [line.strip() for line in lines if line.strip()]
                if len(self.history) > self.max_size:
                    self.history = self.history[-self.max_size :]
                self.current_index = len(self.history)
        except Exception:
            # TODO: Add logging.
            self.history = []
            self.current_index = 0

    def _save_history(self):
        """Save history to file."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                for command in self.history:
                    f.write(f"{command}\n")
        except OSError as e:
            logging.warning("Failed to save history to %s: %s", self.history_file, e)

    def get_stats(self) -> dict[str, int | str | tuple[str, int] | None]:
        """Get history statistics.

        Returns:
            Dictionary with history stats
        """
        if not self.history:
            return {
                "total_commands": 0,
                "unique_commands": 0,
                "most_used": None,
                "history_file": self.history_file,
            }

        # TODO: Should be a collections.Counter
        command_counts: dict[str, int] = {}
        for cmd in self.history:
            base_cmd = cmd.split()[0] if cmd.split() else cmd
            command_counts[base_cmd] = command_counts.get(base_cmd, 0) + 1

        most_used: tuple[str, int] | None = (
            max(command_counts.items(), key=lambda x: x[1]) if command_counts else None
        )

        return {
            "total_commands": len(self.history),
            "unique_commands": len(set(self.history)),
            "most_used": most_used,
            "history_file": self.history_file,
        }

    def expand_history(self, command: str) -> str:
        """Expand history expressions in a command.

        Supports:
        - !! - Repeat last command
        - !n - Execute command number n (1-based)
        - !string - Execute last command starting with string
        - ^old^new - Quick substitution from last command

        Args:
            command: Command string that may contain history expressions

        Returns:
            Expanded command string

        Raises:
            HistoryExpansionError: If history expansion fails
        """
        if not command.strip():
            return command
        if command.startswith("^") and command.count("^") >= 2:
            return self._handle_quick_substitution(command)
        if "!" in command:
            return self._expand_bang_history(command)
        return command

    def _handle_quick_substitution(self, command: str) -> str:
        """Handle ^old^new quick substitution.

        Args:
            command: Command starting with ^ for substitution

        Returns:
            Last command with substitution applied

        Raises:
            HistoryExpansionError: If substitution fails
        """
        if not self.history:
            raise HistoryExpansionError("No previous command for substitution")

        # Parse ^old^new format
        parts = command[1:].split("^", 2)  # Skip first ^, split on remaining ^
        if len(parts) < 2:
            raise HistoryExpansionError("Invalid substitution format. Use ^old^new")

        old_text, new_text = parts
        last_command = self.history[-1]
        if old_text not in last_command:
            raise HistoryExpansionError(
                f"'{old_text}' not found in last command: {last_command}"
            )
        return last_command.replace(old_text, new_text, 1)

    def _expand_bang_history(self, command: str) -> str:
        """Expand ! history expressions in command.

        Args:
            command: Command that may contain ! expressions

        Returns:
            Command with ! expressions expanded

        Raises:
            HistoryExpansionError: If expansion fails
        """
        if not self.history:
            raise HistoryExpansionError("No command history available")
        if command == "!!":
            return self.history[-1]
        if not command.startswith("!") or len(command) <= 1:
            return command
        rest = command[1:]
        if rest.isdigit():
            cmd_num = int(rest)
            if cmd_num < 1 or cmd_num > len(self.history):
                raise HistoryExpansionError(
                    f"Command number {cmd_num} out of range (1-{len(self.history)})"
                )
            return self.history[cmd_num - 1]  # Convert to 0-based index
        for cmd in reversed(self.history):
            if cmd.startswith(rest):
                return cmd
        raise HistoryExpansionError(f"No command found starting with '{rest}'")

    def get_command_number(self, command: str) -> int | None:
        """Get the command number (1-based) for a given command.

        Args:
            command: Command to find

        Returns:
            Command number or None if not found
        """
        try:
            return self.history.index(command) + 1  # Convert to 1-based
        except ValueError:
            return None

    def get_numbered_history(
        self, start: int | None = None, count: int | None = None
    ) -> list[tuple[int, str]]:
        """Get history entries with their command numbers.

        Args:
            start: Starting command number (1-based, None for beginning)
            count: Number of entries to return (None for all remaining)

        Returns:
            List of (command_number, command) tuples
        """
        if not self.history:
            return []

        start_idx = 0 if start is None else max(0, start - 1)  # Convert to 0-based
        end_idx = (
            len(self.history)
            if count is None
            else min(len(self.history), start_idx + count)
        )

        return [
            (i + 1, cmd)
            for i, cmd in enumerate(self.history[start_idx:end_idx], start_idx)
        ]


class HistoryExpansionError(Exception):
    """Exception raised when history expansion fails."""


# Global history instance.
# TODO: This should go into the shell object.
_shell_history: ShellHistory | None = None


def get_shell_history() -> ShellHistory:
    """Get the global shell history instance."""
    global _shell_history
    if _shell_history is None:
        _shell_history = ShellHistory()
    # Type checker workaround - we know _shell_history is not None here
    return _shell_history  # type: ignore[return-value]


def init_shell_history(
    max_size: int = 1000, history_file: str | None = None
) -> ShellHistory:
    """Initialize the global shell history.

    Args:
        max_size: Maximum number of history entries
        history_file: Path to history file

    Returns:
        ShellHistory instance
    """
    global _shell_history
    _shell_history = ShellHistory(max_size, history_file)
    return _shell_history
