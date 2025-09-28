"""Implementation of MoreCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class MoreCommand(Command):
    """Implementation of more command."""

    name = "more"
    help = "View file contents with simple pagination"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """View file contents with simple pagination.

Usage: more [OPTIONS] [FILE...]

Description:
    Display file contents one screen at a time.
    Less featured than 'less' but simpler to use.

Options:
    -d              Show help prompt
    -f              Count logical lines instead of screen lines
    -l              Don't treat form feeds specially
    -s              Squeeze multiple blank lines
    -h, --help      Show this help message

Navigation:
    Space           Next page
    Enter           Next line
    q               Quit
    h               Help

Examples:
    more file.txt
    more -s file.txt
    cat file.txt | more
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the more command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "d": bool,  # show help
                "f": bool,  # logical lines
                "l": bool,  # no form feeds
                "s": bool,  # squeeze blanks
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        show_help = flags.get("d", False)
        flags.get("f", False)  # logical_lines - not implemented
        flags.get("l", False)  # no_form_feeds - not implemented
        squeeze_blanks = flags.get("s", False)

        if not positional_args:
            self.console.print("[red]more: missing file argument[/red]")
            return 1

        file_path = positional_args[0]

        try:
            content = safe_read_file(client, file_path)
            if content is None:
                return 1

            lines = content.splitlines()

            # Process lines based on options
            if squeeze_blanks:
                processed_lines = []
                prev_blank = False
                for line in lines:
                    is_blank = not line.strip()
                    if not (is_blank and prev_blank):
                        processed_lines.append(line)
                    prev_blank = is_blank
                lines = processed_lines

            # Simple pagination
            self._simple_paginate(lines, show_help)
            return 0

        except ops.pebble.PathError:
            self.console.print(
                f"[red]more: cannot open '{file_path}': No such file[/red]"
            )
            return 1
        except Exception as e:
            self.console.print(f"[red]more: {e}[/red]")
            return 1

    def _simple_paginate(self, lines: list[str], show_help: bool):
        """Simple pagination for more command."""
        page_size = 20
        current_line = 0

        while current_line < len(lines):
            # Display current page
            end_line = min(current_line + page_size, len(lines))

            for i in range(current_line, end_line):
                self.console.print(lines[i])

            # Show prompt
            if end_line >= len(lines):
                break

            remaining_percent = int((len(lines) - end_line) / len(lines) * 100)
            prompt = f"--More--({remaining_percent}%)"
            if show_help:
                prompt += " (h for help)"

            self.console.print(f"[dim]{prompt}[/dim]", end="")

            try:
                user_input = input()
                if user_input.lower() == "q":
                    break
                elif user_input.lower() == "h":
                    self.console.print(
                        "\nHelp: Space=next page, Enter=next line, q=quit, h=help"
                    )
                    continue
                elif user_input == "":  # Enter for next line
                    current_line += 1
                else:  # Space or any other key for next page
                    current_line = end_line
            except (EOFError, KeyboardInterrupt):
                break
