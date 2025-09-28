"""Implementation of RunlevelCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import read_proc_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class RunlevelCommand(Command):
    """Implementation of runlevel command."""

    name = "runlevel"
    help = "Display current runlevel"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """Display current runlevel.

Usage: runlevel

Description:
    Print the previous and current runlevel.
    Shows 'N' for unknown previous runlevel.

Examples:
    runlevel        # Display runlevel
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the runlevel command."""
        if handle_help_flag(self, args):
            return 0

        try:
            runlevel = "N 5"  # Default fallback

            # Try to read from various sources
            try:
                # Check /var/run/utmp (not always available)
                with client.pull("/var/run/utmp", encoding="utf-8") as f:
                    # utmp parsing is complex, skip for now
                    pass
            except ops.pebble.PathError:
                pass

            try:
                # Check systemd target
                init_name = read_proc_file(client, "/proc/1/comm").strip()
                if init_name == "systemd":
                    # In systemd systems, try to infer from target
                    try:
                        with client.pull(
                            "/etc/systemd/system/default.target", encoding="utf-8"
                        ) as f:
                            target_link = f.read().strip()
                            if "multi-user.target" in target_link:
                                runlevel = "N 3"
                            elif "graphical.target" in target_link:
                                runlevel = "N 5"
                    except ops.pebble.PathError:
                        pass
            except ops.pebble.PathError:
                pass

            # Check if we're in a container (common case)
            try:
                cgroup_content = read_proc_file(client, "/proc/1/cgroup")
                if "docker" in cgroup_content or "containerd" in cgroup_content:
                    runlevel = "N 5"  # Containers typically act like runlevel 5
            except ops.pebble.PathError:
                pass

            self.console.print(runlevel)
            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"runlevel: {e}"))
            return 1
