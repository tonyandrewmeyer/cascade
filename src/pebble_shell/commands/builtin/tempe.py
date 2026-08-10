"""Tempe command for Cascade.

This module provides implementation for the tempe command that creates
a temporary directory and changes into it.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from ...utils.parser import get_shell_parser
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TempeCommand(Command):
    """Create a temporary directory and change into it."""

    name = "tempe"
    help = "Create a temporary directory and change into it"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Create a temporary directory and change into it.

Usage: tempe [OPTIONS]

Options:
    -h, --help      Show this help message
    -p, --prefix    Prefix for the temporary directory name (default: tmp)
    -q, --quiet     Don't print the directory path

Creates a new temporary directory in /tmp and changes into it.
Useful for quick scratch work.

Examples:
    tempe                   # Create /tmp/tmp.abc123 and enter
    tempe -p mywork         # Create /tmp/mywork.abc123 and enter
    tempe -q                # Create and enter quietly
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the tempe command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "p": str,
                "prefix": str,
                "q": bool,
                "quiet": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        prefix = flags["p"] or flags["prefix"] or "tmp"
        quiet = flags["q"] or flags["quiet"]

        # Generate a unique directory name
        random_suffix = str(uuid.uuid4())[:8]
        dir_name = f"{prefix}.{random_suffix}"
        full_path = f"/tmp/{dir_name}"

        # Create the directory
        try:
            client.make_dir(full_path, make_parents=True)
        except Exception as e:
            self.console.print(f"[red]tempe: cannot create directory '{full_path}': {e}[/red]")
            return 1

        # Change into the directory
        try:
            client.list_files(full_path)  # Verify it's a valid directory
        except ops.pebble.APIError:
            self.console.print(f"[red]tempe: cannot access directory '{full_path}'[/red]")
            return 1

        self.shell.current_directory = full_path
        parser = get_shell_parser()
        parser.update_pwd(full_path)

        if not quiet:
            self.console.print(full_path)

        return 0
