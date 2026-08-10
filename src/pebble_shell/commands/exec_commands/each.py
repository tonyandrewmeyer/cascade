"""Run a command for each line of input.

each is a simpler alternative to xargs that runs a command for each line
from stdin, replacing {} with the line content.
"""

from __future__ import annotations

import shlex
import sys
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class EachCommand(Command):
    """Run a command for each line of input."""

    name = "each"
    help = "Run a command for each line of input"
    category = "Remote Execution"

    def show_help(self):
        """Show command help."""
        help_text = """Run a command for each line of input.

Usage: <input> | each [OPTIONS] "command {}"

Options:
    -h, --help      Show this help message
    -t, --trace     Print each command before executing
    -s, --stop      Stop on first error (exit non-zero)
    -p, --prompt    Prompt before executing each command
    -n, --dry-run   Show commands without executing them

The command must contain {} which will be replaced with each input line.

Examples:
    echo -e "file1\\nfile2" | each "cat {}"
    ls *.txt | each "wc -l {}"
    find . -name "*.log" | each "rm {}"
    cat urls.txt | each -t "curl {}"
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the each command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "t": bool,
                "trace": bool,
                "s": bool,
                "stop": bool,
                "p": bool,
                "prompt": bool,
                "n": bool,
                "dry-run": bool,
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
            self.console.print("[red]each: missing command argument[/red]")
            self.console.print("Usage: <input> | each \"command {}\"")
            return 1

        # Join positional args to form the command template
        command_template = " ".join(positional_args)

        if "{}" not in command_template:
            self.console.print("[red]each: command must contain {} placeholder[/red]")
            self.console.print("Example: each \"cat {}\"")
            return 1

        trace = flags["t"] or flags["trace"]
        stop_on_error = flags["s"] or flags["stop"]
        prompt = flags["p"] or flags["prompt"]
        dry_run = flags["n"] or flags["dry-run"]

        # Read from stdin
        if sys.stdin.isatty():
            self.console.print(
                "[yellow]each: no input provided (pipe data to this command)[/yellow]"
            )
            return 1

        input_text = sys.stdin.read()
        if not input_text.strip():
            # No input, nothing to do
            return 0

        # Split on newlines (handle both \n and \r\n)
        lines = input_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        exit_code = 0
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Build the command by replacing {} with the quoted line
            # Use shlex.quote to properly escape the argument
            quoted_arg = shlex.quote(line)
            command_str = command_template.replace("{}", quoted_arg)

            if trace or dry_run:
                self.console.print(f"[dim]+ {command_str}[/dim]")

            if dry_run:
                continue

            if prompt:
                try:
                    response = input(f"Execute '{command_str}'? (y/n) ")
                    if response.lower() not in ["y", "yes"]:
                        continue
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n[yellow]each: interrupted[/yellow]")
                    return 1

            # Execute the command
            result_code = self._execute_command(client, command_str)

            if result_code != 0:
                exit_code = result_code
                if stop_on_error:
                    return exit_code

        return exit_code

    def _execute_command(self, client: ClientType, command_str: str) -> int:
        """Execute a command string on the remote system."""
        # Use sh -c to execute the command string
        # This handles pipes, redirects, and complex commands
        cmd = ["sh", "-c", command_str]

        try:
            process = client.exec(cmd)
            stdout, stderr = process.wait_output()
            if stdout:
                self.console.print(stdout, end="")
            if stderr:
                self.shell.error_console.print(stderr, end="")
            return 0
        except ops.pebble.ExecError as e:
            if hasattr(e, "stdout") and e.stdout:
                self.console.print(e.stdout, end="")
            if hasattr(e, "stderr") and e.stderr:
                self.shell.error_console.print(e.stderr, end="")
            return e.exit_code
        except ops.pebble.APIError as e:
            self.console.print(f"[red]each: command failed: {e}[/red]")
            return 1
