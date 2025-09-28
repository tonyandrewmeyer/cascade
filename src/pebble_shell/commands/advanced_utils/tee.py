"""Implementation of TeeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TeeCommand(Command):
    """Implementation of tee command."""

    name = "tee"
    help = "Copy input to both stdout and files"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Copy input to both stdout and files.

Usage: tee [OPTIONS] [FILE...]

Description:
    Read from standard input and write to both standard output and files.

Options:
    -a, --append    Append to files instead of overwriting
    -i, --ignore-interrupts  Ignore interrupt signals
    -h, --help      Show this help message

Examples:
    echo "hello" | tee output.txt
    ls -la | tee -a logfile.txt
    command | tee file1.txt file2.txt
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the tee command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "a": bool,  # append
                "append": bool,
                "i": bool,  # ignore interrupts
                "ignore-interrupts": bool,
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        append_mode = flags.get("a", False) or flags.get("append", False)
        ignore_interrupts = flags.get("i", False) or flags.get(
            "ignore-interrupts", False
        )
        output_files = positional_args

        try:
            # TODO: Finish implementation!
            self.console.print(
                "[yellow]tee: reading from stdin (enter text, Ctrl+D to end):[/yellow]"
            )

            input_lines = []
            try:
                while True:
                    try:
                        line = input()
                        input_lines.append(line + "\n")
                        # Echo to stdout immediately
                        self.console.print(line)
                    except EOFError:  # noqa: PERF203  # needed for input handling
                        break
                    except KeyboardInterrupt:
                        if not ignore_interrupts:
                            raise
            except KeyboardInterrupt:
                if not ignore_interrupts:
                    self.console.print("\n[yellow]tee: interrupted[/yellow]")
                    return 1

            # Write to output files
            content = "".join(input_lines)

            for file_path in output_files:
                try:
                    if append_mode:
                        # Read existing content first
                        existing_content = safe_read_file(client, file_path)
                        if existing_content is None:
                            existing_content = ""

                        with client.push(file_path, encoding="utf-8") as f:
                            f.write(existing_content + content)
                    else:
                        with client.push(file_path, encoding="utf-8") as f:
                            f.write(content)

                    self.console.print(f"[green]tee: written to {file_path}[/green]")

                except Exception as e:  # noqa: PERF203  # needed for robust file processing
                    self.console.print(
                        f"[red]tee: failed to write {file_path}: {e}[/red]"
                    )
                    return 1

            return 0

        except Exception as e:
            self.console.print(f"[red]tee: {e}[/red]")
            return 1
