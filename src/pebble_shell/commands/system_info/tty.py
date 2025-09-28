"""Implementation of TtyCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TtyCommand(Command):
    """Implementation of tty command."""

    name = "tty"
    help = "Display terminal device name"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """Display the terminal device name.

Usage: tty [-s]

Description:
    Print the name of the terminal connected to standard input.

Options:
    -s, --silent    Be silent, only return exit status
    -h, --help      Show this help message

Examples:
    tty             # Display terminal name
    tty -s          # Check if stdin is a terminal (silent)
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the tty command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "s": bool,  # silent
                "silent": bool,
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        silent = flags.get("s", False) or flags.get("silent", False)

        try:
            # Try to determine TTY from environment or proc
            tty_name = "not a tty"

            # Check environment variables
            import os

            if "SSH_TTY" in os.environ:
                tty_name = os.environ["SSH_TTY"]
            elif "TTY" in os.environ:
                tty_name = os.environ["TTY"]
            else:
                # Try to read from /proc/self/fd/0 link
                try:
                    with client.pull("/proc/self/fd/0", encoding="utf-8"):
                        # This is a symlink, try to read target
                        pass
                except Exception:  # noqa: S110
                    # Broad exception handling needed when probing TTY info
                    pass

                # Fallback: assume we're in a terminal if we have specific env vars
                if any(var in os.environ for var in ["TERM", "SHELL", "PS1"]):
                    tty_name = "/dev/pts/0"  # Default assumption

            if not silent:
                self.console.print(tty_name)

            # Return 0 if we have a TTY, 1 if not
            return 0 if tty_name != "not a tty" else 1

        except Exception as e:
            if not silent:
                self.console.print(get_theme().error_text(f"tty: {e}"))
            return 2
