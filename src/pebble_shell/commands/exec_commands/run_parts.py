"""Implementation of run-parts command."""

from __future__ import annotations

import string
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class RunPartsCommand(Command):
    """Implementation of run-parts command."""

    name = "run-parts"
    help = "Run all executable files in a directory"
    category = "Process Management"

    def __init__(self, shell: PebbleShell) -> None:
        super().__init__(shell)

    def show_help(self):
        """Show command help."""
        help_text = """Run all executable files in a directory.

Usage: run-parts [OPTIONS] DIRECTORY

Description:
    Run all executable files in DIRECTORY in lexicographic order.
    Commonly used for running scripts in /etc/cron.daily, etc.

Options:
    --test          Print names of files that would be run, but don't run them
    --list          Print names of files that would be run (same as --test)
    -v, --verbose   Print name of each file before running it
    --report        Print name of each file as it is run
    --exit-on-error Exit if any script fails
    --arg ARG       Pass ARG to each script
    -h, --help      Show this help message

Examples:
    run-parts /etc/cron.daily       # Run all daily cron jobs
    run-parts --test /etc/cron.d    # Show what would be run
    run-parts -v /usr/local/bin     # Run with verbose output
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the run-parts command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "test": bool,
                "list": bool,
                "v": bool,
                "verbose": bool,
                "report": bool,
                "exit-on-error": bool,
                "arg": str,
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if not positional_args:
            self.console.print("[red]run-parts: missing directory[/red]")
            return 1

        directory = positional_args[0]
        test_mode = flags.get("test", False) or flags.get("list", False)
        verbose = flags.get("v", False) or flags.get("verbose", False)
        report = flags.get("report", False)
        exit_on_error = flags.get("exit-on-error", False)
        extra_arg = flags.get("arg")

        try:
            # List files in the directory
            try:
                files = client.list_files(directory)
            except Exception as e:
                self.console.print(
                    f"[red]run-parts: cannot read directory '{directory}': {e}[/red]"
                )
                return 1

            # Filter and sort executable files (or treat all as potentially executable)
            executable_files = [
                file_info.name
                for file_info in files
                if file_info.type == ops.pebble.FileType.FILE
                and self._is_valid_run_parts_file(file_info.name)
            ]

            # Sort lexicographically
            executable_files.sort()

            if not executable_files:
                if verbose:
                    self.console.print(
                        f"run-parts: no executable files found in {directory}"
                    )
                return 0

            # Test mode - just list files
            if test_mode:
                for filename in executable_files:
                    file_path = f"{directory.rstrip('/')}/{filename}"
                    self.console.print(file_path)
                return 0

            # Execute each file
            overall_exit_code = 0
            for filename in executable_files:
                file_path = f"{directory.rstrip('/')}/{filename}"

                if verbose or report:
                    self.console.print(f"run-parts: executing {file_path}")

                try:
                    # Build command arguments
                    command = [file_path]
                    if extra_arg:
                        command.append(extra_arg)

                    # Execute the script
                    process = client.exec(
                        command,
                        working_dir="/",
                        user_id=0,
                        user="root",
                        group_id=0,
                        group="root",
                    )

                    # Stream output
                    for line in process.stdout:
                        self.console.print(line, end="")

                    # Wait for completion
                    process.wait()
                    exit_code = process.exit_code or 0

                    if exit_code != 0:
                        overall_exit_code = exit_code
                        if verbose:
                            self.console.print(
                                f"[yellow]run-parts: {file_path} exited with code {exit_code}[/yellow]"
                            )

                        if exit_on_error:
                            self.console.print(
                                f"[red]run-parts: stopping due to error in {file_path}[/red]"
                            )
                            return exit_code

                except Exception as e:
                    self.console.print(
                        f"[red]run-parts: failed to execute {file_path}: {e}[/red]"
                    )
                    overall_exit_code = 1
                    if exit_on_error:
                        return 1

            return overall_exit_code

        except Exception as e:
            self.console.print(f"[red]run-parts: {e}[/red]")
            return 1

    def _is_valid_run_parts_file(self, filename: str) -> bool:
        """Check if filename is valid for run-parts execution."""
        # run-parts typically ignores files with certain patterns
        # Skip files that start with . or end with ~ or contain ,
        if filename.startswith("."):
            return False
        if filename.endswith("~"):
            return False
        if "," in filename:
            return False
        if filename.endswith(".disabled"):
            return False
        if filename.endswith(".dpkg-old"):
            return False
        if filename.endswith(".dpkg-new"):
            return False
        if filename.endswith(".rpmsave"):
            return False
        if filename.endswith(".rpmnew"):
            return False

        # Only allow alphanumeric, underscore, hyphen, and dot
        allowed_chars = string.ascii_letters + string.digits + "_-."
        return all(c in allowed_chars for c in filename)
