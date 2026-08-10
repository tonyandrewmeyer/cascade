"""Mkcd command for Cascade.

This module provides implementation for the mkcd command that creates
a directory and changes into it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils import resolve_path
from ...utils.command_helpers import parse_flags
from ...utils.parser import get_shell_parser
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class MkcdCommand(Command):
    """Create a directory and change into it."""

    name = "mkcd"
    help = "Create a directory and change into it"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Create a directory and change into it.

Usage: mkcd [OPTIONS] DIRECTORY

Options:
    -h, --help      Show this help message
    -p              Create parent directories as needed

Combines mkdir and cd into a single command.

Examples:
    mkcd myproject          # Create and enter 'myproject'
    mkcd -p a/b/c           # Create nested directories and enter
    mkcd /tmp/workspace     # Create with absolute path and enter
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the mkcd command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "p": bool,
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
            self.console.print("[red]mkcd: missing directory argument[/red]")
            return 1

        directory = positional_args[0]
        make_parents = flags["p"]

        # Resolve the path
        full_path = resolve_path(
            self.shell.current_directory, directory, self.shell.home_dir
        )

        # Create the directory
        try:
            client.make_dir(full_path, make_parents=make_parents)
        except ops.pebble.PathError as e:
            if "exists" in str(e).lower():
                # Directory already exists, that's fine - we'll just cd into it
                pass
            else:
                self.console.print(f"[red]mkcd: cannot create directory '{full_path}': {e}[/red]")
                return 1
        except Exception as e:
            self.console.print(f"[red]mkcd: cannot create directory '{full_path}': {e}[/red]")
            return 1

        # Change into the directory
        try:
            client.list_files(full_path)  # Verify it's a valid directory
        except ops.pebble.APIError:
            self.console.print(f"[red]mkcd: cannot access directory '{full_path}'[/red]")
            return 1

        self.shell.current_directory = full_path
        parser = get_shell_parser()
        parser.update_pwd(full_path)

        self.console.print(f"[green]Created and entered:[/green] {full_path}")
        return 0
