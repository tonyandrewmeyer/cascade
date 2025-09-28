"""Implementation of LessCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LessCommand(Command):
    """Implementation of less command."""

    name = "less"
    help = "View file contents with pagination"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """View file contents with pagination.

Usage: less [OPTIONS] [FILE...]

Description:
    Display file contents one screen at a time.
    Navigate with arrow keys, page up/down, or commands.

Options:
    -n              Don't use line numbers
    -S              Don't wrap long lines
    -i              Ignore case in searches
    -X              Don't clear screen on exit
    -h, --help      Show this help message

Navigation:
    Space/PageDown  Next page
    b/PageUp        Previous page
    j/Down          Next line
    k/Up            Previous line
    g/Home          Go to beginning
    G/End           Go to end
    q               Quit
    /pattern        Search forward
    ?pattern        Search backward
    n               Next search result
    N               Previous search result

Examples:
    less file.txt
    less -S longlines.txt
    less /var/log/syslog
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the less command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "n": bool,  # no line numbers
                "S": bool,  # no wrap
                "i": bool,  # ignore case
                "X": bool,  # no clear screen
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        no_line_numbers = flags.get("n", False)
        no_wrap = flags.get("S", False)
        ignore_case = flags.get("i", False)
        no_clear = flags.get("X", False)

        if not positional_args:
            self.console.print("[red]less: missing file argument[/red]")
            return 1

        file_path = positional_args[0]

        try:
            # Read file content
            content = safe_read_file(client, file_path)
            if content is None:
                return 1

            lines = content.splitlines()

            # Simple pagination implementation
            self._paginate_content(
                lines, no_line_numbers, no_wrap, ignore_case, no_clear
            )
            return 0

        except ops.pebble.PathError:
            self.console.print(
                f"[red]less: cannot open '{file_path}': No such file[/red]"
            )
            return 1
        except Exception as e:
            self.console.print(f"[red]less: {e}[/red]")
            return 1

    def _paginate_content(
        self,
        lines: list[str],
        no_line_numbers: bool,
        no_wrap: bool,
        ignore_case: bool,
        no_clear: bool,
    ):
        """Simple pagination of content."""
        # This is a simplified implementation - real less is much more complex
        page_size = 20  # Number of lines per page
        current_line = 0
        search_pattern = None

        while current_line < len(lines):
            # Display current page
            end_line = min(current_line + page_size, len(lines))

            for i in range(current_line, end_line):
                line = lines[i]
                if not no_wrap and len(line) > 80:
                    line = line[:77] + "..."

                if not no_line_numbers:
                    self.console.print(f"{i + 1:6d}: {line}")
                else:
                    self.console.print(line)

            # Show status line
            if end_line >= len(lines):
                self.console.print(
                    f"[dim](END) lines {current_line + 1}-{len(lines)} of {len(lines)}[/dim]"
                )
                break
            else:
                self.console.print(
                    f"[dim]:{current_line + 1}-{end_line} of {len(lines)} (press 'q' to quit, space for next page)[/dim]"
                )

            # Wait for user input (simplified)
            try:
                user_input = input()
                if user_input.lower() == "q":
                    break
                elif user_input == "":  # Space or enter for next page
                    current_line = end_line
                elif user_input.startswith("/"):
                    # Simple search
                    search_pattern = user_input[1:]
                    # Find next occurrence
                    found = False
                    for i in range(current_line + 1, len(lines)):
                        if (
                            ignore_case and search_pattern.lower() in lines[i].lower()
                        ) or search_pattern in lines[i]:
                            current_line = max(0, i - page_size // 2)
                            found = True
                            break
                    if not found:
                        self.console.print(
                            f"[yellow]Pattern not found: {search_pattern}[/yellow]"
                        )
                else:
                    current_line = end_line
            except (EOFError, KeyboardInterrupt):
                break
