"""Implementation of XargsCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class XargsCommand(Command):
    """Implementation of xargs command."""

    name = "xargs"
    help = "Build and execute command lines from standard input"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Build and execute command lines from standard input.

Usage: xargs [OPTIONS] [COMMAND [ARG...]]

Description:
    Read space/newline-separated arguments from stdin and execute command.

Options:
    -n MAX          Use at most MAX arguments per command line
    -I REPLACE      Replace occurrences of REPLACE with arguments
    -d DELIM        Use DELIM as input delimiter
    -p              Prompt before executing each command
    -t              Print commands before executing
    -r              Don't run command if input is empty
    -0              Input items are null-terminated
    -h, --help      Show this help message

Examples:
    echo "file1 file2" | xargs ls -la
    find . -name "*.tmp" | xargs rm
    echo "arg1 arg2" | xargs -I {} echo "processing {}"
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the xargs command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "n": int,  # max args
                "I": str,  # replace string
                "d": str,  # delimiter
                "p": bool,  # prompt
                "t": bool,  # trace
                "r": bool,  # no-run-if-empty
                "0": bool,  # null terminated
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        max_args = flags.get("n")
        replace_str = flags.get("I")
        delimiter = flags.get("d", None)
        prompt = flags.get("p", False)
        trace = flags.get("t", False)
        no_run_if_empty = flags.get("r", False)
        null_terminated = flags.get("0", False)

        command_template = positional_args if positional_args else ["echo"]

        try:
            # Read input (simulated for this implementation)
            self.console.print(
                "[yellow]xargs: reading from stdin (enter arguments, Ctrl+D to end):[/yellow]"
            )

            input_text = ""
            try:
                while True:
                    try:
                        line = input()
                        input_text += line + "\n"
                    except EOFError:  # noqa: PERF203  # needed for input handling
                        break
            except KeyboardInterrupt:
                self.console.print("\n[yellow]xargs: interrupted[/yellow]")
                return 1

            if not input_text.strip() and no_run_if_empty:
                return 0

            # Parse input arguments
            if null_terminated:
                input_args = input_text.split("\0")
            elif delimiter:
                input_args = input_text.split(delimiter)
            else:
                # Split on whitespace
                input_args = input_text.split()

            # Filter empty arguments
            input_args = [arg for arg in input_args if arg.strip()]

            if not input_args and no_run_if_empty:
                return 0

            # Execute commands
            if replace_str:
                # Replace mode - one command per argument
                for arg in input_args:
                    command = [
                        part.replace(replace_str, arg) for part in command_template
                    ]

                    if trace:
                        self.console.print(f"+ {' '.join(command)}")

                    if prompt:
                        response = input(f"Execute '{' '.join(command)}'? (y/n) ")
                        if response.lower() not in ["y", "yes"]:
                            continue

                    # Execute command (simulate execution)
                    self._execute_command(client, command)
            else:
                # Batch mode
                if max_args:
                    # Split into batches
                    for i in range(0, len(input_args), max_args):
                        batch = input_args[i : i + max_args]
                        command = command_template + batch

                        if trace:
                            self.console.print(f"+ {' '.join(command)}")

                        if prompt:
                            response = input(f"Execute '{' '.join(command)}'? (y/n) ")
                            if response.lower() not in ["y", "yes"]:
                                continue

                        self._execute_command(client, command)
                else:
                    # All arguments at once
                    command = command_template + input_args

                    if trace:
                        self.console.print(f"+ {' '.join(command)}")

                    if prompt:
                        response = input(f"Execute '{' '.join(command)}'? (y/n) ")
                        if response.lower() not in ["y", "yes"]:
                            return 0

                    self._execute_command(client, command)

            return 0

        except Exception as e:
            self.console.print(f"[red]xargs: {e}[/red]")
            return 1

    def _execute_command(self, client: ClientType, command: list[str]):
        """Execute a command (simulated)."""
        # TODO: Implement this!
        self.console.print(f"[green]Would execute: {' '.join(command)}[/green]")
