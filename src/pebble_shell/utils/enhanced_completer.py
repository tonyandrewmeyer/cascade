"""Enhanced tab completion for Cascade shell."""

from __future__ import annotations

import difflib
import os
import readline
from typing import TYPE_CHECKING, Any

import ops

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..commands import AliasCommand
    from ..shell import PebbleShell


class EnhancedCompleter:
    """Enhanced tab completion with remote file support and command-specific completion."""

    def __init__(
        self, shell: PebbleShell, commands: dict[str, Any], alias_command: AliasCommand
    ):
        self.shell = shell
        self.client = shell.client
        self.commands = commands
        self.alias_command = alias_command
        self.command_names = [*list(commands.keys()), "help", "exit", "clear"]
        self.console = shell.console

        self.command_completions: dict[str, Callable[[str, list[str]], list[str]]] = {
            "pgrep": self._complete_process_names,
            "pebble-start": self._complete_pebble_services,
            "pebble-stop": self._complete_pebble_services,
            "pebble-restart": self._complete_pebble_services,
            "pebble-signal": self._complete_pebble_services,
            "pebble-check": self._complete_pebble_checks,
            "pebble-notice": self._complete_pebble_notices,
            "cd": self._complete_directories,
            "ls": self._complete_paths,
            "cat": self._complete_files,
            "head": self._complete_files,
            "tail": self._complete_files,
            "diff": self._complete_files,
            "cp": self._complete_paths,
            "mv": self._complete_paths,
            "rm": self._complete_paths,
            "stat": self._complete_paths,
            "find": self._complete_directories,
            "grep": self._complete_files,
            "mount": self._complete_mount_points,
        }

        self.fuzzy_threshold = 0.6

    def complete(self, text: str, state: int) -> str | None:
        """Main completion function for readline.

        Args:
            text: Text to complete
            state: Completion state

        Returns:
            Completion suggestion or None
        """
        try:
            if state == 0:
                # First call, generate completion list
                self.matches = self._generate_completions(text)
                self.matches = sorted(self.matches)

            if state < len(self.matches):
                return self.matches[state]
            return None
        except Exception:
            # Silently handle completion errors.
            return None

    def _generate_completions(self, text: str) -> list[str]:
        """Generate completion suggestions based on context."""
        # Parse the current line to understand context:
        line = self._get_current_line()
        parts = line.lstrip().split()

        if not parts or (len(parts) == 1 and not line.endswith(" ")):
            # Completing command name:
            return self._complete_command(text)
        # Completing arguments:
        command = parts[0]
        return self._complete_argument(command, parts, text)

    def _get_current_line(self) -> str:
        """Get the current line from readline."""
        return readline.get_line_buffer()

    def _complete_command(self, text: str) -> list[str]:
        """Complete command names with fuzzy matching."""
        matches: list[str] = []

        matches = [cmd for cmd in self.command_names if cmd.startswith(text)]
        matches.extend(
            alias for alias in self.alias_command.aliases if alias.startswith(text)
        )
        # Fuzzy matches if no exact matches:
        if not matches and text:
            matches.extend(
                cmd for cmd in self.command_names if self._fuzzy_match(text, cmd)
            )

        return matches

    def _complete_argument(
        self, command: str, parts: list[str], text: str
    ) -> list[str]:
        """Complete command arguments based on command type."""
        current_arg = (text if text else parts[-1]) if len(parts) > 1 else text

        # Check for command-specific completion:
        if command in self.command_completions:
            return self.command_completions[command](current_arg, parts)

        # Default to path completion:
        return self._complete_paths(current_arg, parts)

    def _complete_process_names(self, text: str, parts: list[str]) -> list[str]:
        """Complete process names for pgrep command."""
        matches: list[str] = []
        proc_entries = self.client.list_files("/proc")
        pids = [entry.name for entry in proc_entries if entry.name.isdigit()]

        for pid in pids:
            try:
                with self.client.pull(f"/proc/{pid}/comm") as file:
                    comm = file.read().strip()
            except ops.pebble.PathError:
                continue
            if isinstance(comm, str) and comm.startswith(text):
                matches.append(comm)

        return list(set(matches))

    def _complete_pebble_services(self, text: str, parts: list[str]) -> list[str]:
        """Complete Pebble service names."""
        services = self.client.get_services()
        return [service.name for service in services if service.name.startswith(text)]

    def _complete_pebble_checks(self, text: str, parts: list[str]) -> list[str]:
        """Complete Pebble check names."""
        checks = self.client.get_checks()
        return [check.name for check in checks if check.name.startswith(text)]

    def _complete_pebble_notices(self, text: str, parts: list[str]) -> list[str]:
        """Complete Pebble notice IDs."""
        notices = self.client.get_notices()
        matches: list[str] = []
        for notice in notices:
            notice_id = str(notice.id)
            if notice_id.startswith(text):
                matches.append(notice_id)
        return matches

    def _complete_mount_points(self, text: str, parts: list[str]) -> list[str]:
        """Complete mount points for mount command."""
        with self.client.pull("/proc/mounts") as file:
            content = file.read()
        assert isinstance(content, str)

        matches: list[str] = []
        for line in content.splitlines():
            if not line.strip():
                continue
            parts_mount = line.split()
            if len(parts_mount) < 2:
                continue
            mount_point = parts_mount[1]
            if mount_point.startswith(text):
                matches.append(mount_point)

        return list(set(matches))  # Remove duplicates

    def _complete_paths(self, text: str, parts: list[str]) -> list[str]:
        """Complete file and directory paths."""
        if not text:
            text = "/"

        # Handle relative paths:
        if not text.startswith("/"):
            text = "/" + text

        # Get the directory to list:
        if text.endswith("/"):
            dir_path = text
            prefix = text
        else:
            dir_path = os.path.dirname(text)
            prefix = os.path.dirname(text) + "/"
            if prefix == "//":
                prefix = "/"

        try:
            entries = self.client.list_files(dir_path)
        except Exception:
            return []

        matches: list[str] = []
        for entry in entries:
            entry_name = entry.name
            full_path = f"{prefix}{entry_name}"
            if full_path.startswith(text):
                if entry.type == ops.pebble.FileType.DIRECTORY:
                    matches.append(full_path + "/")
                else:
                    matches.append(full_path)
        return matches

    def _complete_directories(self, text: str, parts: list[str]) -> list[str]:
        """Complete only directories."""
        path_matches = self._complete_paths(text, parts)
        return [match for match in path_matches if match.endswith("/")]

    def _complete_files(self, text: str, parts: list[str]) -> list[str]:
        """Complete only files (not directories)."""
        path_matches = self._complete_paths(text, parts)
        return [match for match in path_matches if not match.endswith("/")]

    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """Check if pattern fuzzy matches text."""
        if not pattern:
            return True

        # Simple fuzzy matching using difflib:
        similarity = difflib.SequenceMatcher(
            None, pattern.lower(), text.lower()
        ).ratio()
        return similarity >= self.fuzzy_threshold

    def get_completion_hints(self, command: str) -> list[str]:
        """Get completion hints for a command."""
        hints = {
            "pgrep": ["-f", "-u", "process_name"],
            "pkill": ["-f", "-u", "process_name"],
            "kill": ["-9", "process_id"],
            "pebble-start": ["service_name"],
            "pebble-stop": ["service_name"],
            "pebble-restart": ["service_name"],
            "cd": ["directory_path"],
            "ls": ["-la", "-l", "directory_path"],
            "cat": ["file_path"],
            "head": ["-n", "file_path"],
            "tail": ["-f", "-n", "file_path"],
            "diff": ["-r", "file1", "file2"],
            "cp": ["source", "destination"],
            "mv": ["source", "destination"],
            "rm": ["-rf", "file_or_directory"],
            "grep": ["-r", "pattern", "file_or_directory"],
            "mount": ["device", "mount_point"],
        }

        return hints.get(command, [])

    def show_completion_help(self, command: str):
        """Show completion help for a command."""
        hints = self.get_completion_hints(command)
        if hints:
            self.console.print(f"[cyan]Completion hints for '{command}':[/cyan]")
            for hint in hints:
                self.console.print(f"  [yellow]{hint}[/yellow]")
