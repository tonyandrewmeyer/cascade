"""Change current directory."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops
from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from ...utils.parser import get_shell_parser
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CdCommand(Command):
    """Change current directory."""

    name = "cd"
    help = "Change directory. Usage: cd [path]. If no path is given, changes to home directory."
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute cd command."""
        # Handle help flag
        if handle_help_flag(self, args):
            return 0

        # cd with no args goes to home directory.
        target_dir = "~" if len(args) == 0 else args[0]

        current_dir = self.shell.current_directory

        # Handle relative paths.
        if not target_dir.startswith("/") and not target_dir.startswith("~"):
            if current_dir == "/":
                target_dir = "/" + target_dir
            else:
                target_dir = current_dir + "/" + target_dir

        # Normalise path (handle .., ., and so on).
        target_dir = self._normalise_path(target_dir)

        # If we can list it, it's a valid directory.
        try:
            client.list_files(target_dir)
        except ops.pebble.APIError:
            self.console.print(
                Panel(
                    f"Error: No such directory: {target_dir}",
                    title="[b red]cd Error[/b red]",
                    style="red",
                )
            )
            return 1
        self.shell.current_directory = target_dir

        parser = get_shell_parser()
        parser.update_pwd(target_dir)
        return 0

    def _normalise_path(self, path: str) -> str:
        """Normalise a file path."""
        if path.startswith("~"):
            path = self.shell.home_dir + path[1:]

        parts: list[str] = []
        for part in path.split("/"):
            if part == "" or part == ".":
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)

        if not parts:
            return "/"
        return "/" + "/".join(parts)
