"""Implementation of envdir command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class EnvdirCommand(Command):
    """Implementation of envdir command."""

    name = "envdir"
    help = "Run program with environment variables from directory"
    category = "Process Management"

    def show_help(self):
        """Show command help."""
        help_text = """Run program with environment variables from directory.

Usage: envdir DIR PROGRAM [ARGS...]

Description:
    Run PROGRAM with environment variables set from files in DIR.
    Each file in DIR becomes an environment variable:
    - Filename = variable name
    - File content = variable value

Options:
    -h, --help      Show this help message

Examples:
    envdir /etc/env myprogram       # Run with env vars from /etc/env
    envdir ./config ./script.sh     # Run script with config vars
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the envdir command."""
        if handle_help_flag(self, args):
            return 0

        if len(args) < 2:
            self.console.print("[red]envdir: missing directory or program[/red]")
            self.console.print("Usage: envdir DIR PROGRAM [ARGS...]")
            return 1

        env_dir = args[0]
        program = args[1]
        program_args = args[2:]

        try:
            # List files in the environment directory
            try:
                files = client.list_files(env_dir)
            except Exception as e:
                self.console.print(
                    f"[red]envdir: cannot read directory '{env_dir}': {e}[/red]"
                )
                return 1

            # Read environment variables from files
            env_vars = {}
            for file_info in files:
                if file_info.type == ops.pebble.FileType.FILE:
                    file_path = f"{env_dir.rstrip('/')}/{file_info.name}"
                    content = safe_read_file(client, file_path)
                    if content is not None:
                        # Use filename as env var name, content as value
                        # Remove trailing newlines as per envdir behavior
                        env_vars[file_info.name] = content.rstrip("\n\r")

            # Execute the program with environment variables
            full_command = [program, *program_args]

            try:
                process = client.exec(
                    full_command,
                    environment=env_vars,
                    working_dir="/",
                    user_id=0,
                    user="root",
                    group_id=0,
                    group="root",
                )

                # Stream output
                for line in process.stdout:
                    self.console.print(line, end="")

                # Wait for completion and get exit code
                process.wait()
                return process.exit_code or 0

            except Exception as e:
                self.console.print(
                    f"[red]envdir: failed to execute '{program}': {e}[/red]"
                )
                return 127

        except Exception as e:
            self.console.print(f"[red]envdir: {e}[/red]")
            return 1
