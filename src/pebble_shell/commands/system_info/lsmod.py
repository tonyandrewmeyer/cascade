"""Implementation of LsmodCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import read_proc_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LsmodCommand(Command):
    """Implementation of lsmod command."""

    name = "lsmod"
    help = "List loaded kernel modules"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """List loaded kernel modules.

Usage: lsmod

Description:
    Display information about loaded kernel modules.
    Shows module name, size, and usage count.

Examples:
    lsmod           # List all loaded modules
        """
        self.console.print(help_text)

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the lsmod command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Read /proc/modules to get module information
            content = read_proc_file(client, "/proc/modules")

            if not content.strip():
                self.console.print(get_theme().warning_text("No modules loaded"))
                return 0

            # Parse and display module information
            self.console.print("Module                  Size  Used by")

            for line in content.splitlines():
                parts = line.strip().split()
                if len(parts) >= 3:
                    module_name = parts[0]
                    module_size = parts[1]
                    ref_count = parts[2]
                    used_by = " ".join(parts[3:]) if len(parts) > 3 else ""

                    # Format the output similar to lsmod
                    self.console.print(
                        f"{module_name:<22} {module_size:>8} {ref_count:>2} {used_by}"
                    )

            return 0

        except ops.pebble.PathError:
            self.console.print(get_theme().warning_text("/proc/modules not accessible"))
            return 1
        except Exception as e:
            self.console.print(get_theme().error_text(f"lsmod: {e}"))
            return 1
