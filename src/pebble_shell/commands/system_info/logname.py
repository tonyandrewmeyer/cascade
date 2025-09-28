"""Implementation of LognameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file
from ...utils.proc_reader import read_proc_file
from ...utils.theme import get_theme
from .._base import Command
from .exceptions import SystemInfoError

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LognameCommand(Command):
    """Implementation of logname command."""

    name = "logname"
    help = "Display the current user's login name"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """Display the current user's login name.

Usage: logname [OPTIONS]

Options:
    -h, --help      Show this help message
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the logname command."""
        self.client = client
        if handle_help_flag(self, args):
            return 0

        try:
            # Get the login name
            login_name = self._get_login_name()
            self.console.print(login_name)
            return 0
        except SystemInfoError as e:
            self.console.print(get_theme().error_text(f"logname: {e}"))
            return 1

    def _get_help_text(self) -> str:
        """Get help text for the logname command."""
        return """
logname - display user's login name

USAGE:
    logname

DESCRIPTION:
    Print the name of the current user.

EXAMPLES:
    logname         # Display login name
"""

    def _get_login_name(self) -> str:
        """Get the user's login name from the remote system."""
        try:
            # Try to get login name from environment in /proc/1/environ
            try:
                environ_data = read_proc_file(self.client, "/proc/1/environ")

                # Parse environment variables
                env_vars = {}
                for item in environ_data.split("\0"):
                    if "=" in item:
                        key, value = item.split("=", 1)
                        env_vars[key] = value

                # Try LOGNAME first, then USER
                for var_name in ["LOGNAME", "USER"]:
                    if env_vars.get(var_name):
                        return env_vars[var_name]
            except ops.pebble.PathError:
                pass

            # Try to get user from /etc/passwd for current UID
            try:
                # First get current UID from /proc/self/status
                uid = None
                try:
                    status_content = read_proc_file(self.client, "/proc/self/status")

                    for line in status_content.splitlines():
                        if line.startswith("Uid:"):
                            uid = line.split()[1]  # Real UID
                            break
                except ops.pebble.PathError:
                    pass

                if uid:
                    # Look up user in /etc/passwd
                    try:
                        passwd_content = (
                            safe_read_file(self.client, "/etc/passwd") or ""
                        )

                        for line in passwd_content.splitlines():
                            if line.strip():
                                parts = line.split(":")
                                if len(parts) >= 3 and parts[2] == uid:
                                    return parts[0]  # Username
                    except ops.pebble.PathError:
                        pass
            except Exception:  # noqa: S110
                # Broad exception handling needed when reading user info
                pass

            # Fallback: return "root" as it's common in containers
            return "root"

        except Exception as e:
            raise SystemInfoError(f"Failed to get login name: {e}") from e
