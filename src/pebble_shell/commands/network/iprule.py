"""Implementation of iprule command (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ...utils.command_helpers import handle_help_flag, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

    from pebble_shell.shell import PebbleShell

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class IpruleCommand(Command):
    """Implementation of iprule command (read-only)."""

    name = "iprule"
    help = "Display IP routing rules"
    category = "Network"

    def show_help(self):
        """Show command help."""
        help_text = """Display IP routing rules.

Usage: iprule [OPTIONS]

Description:
    Display routing policy rules. Read-only version.
    Simplified version of 'ip rule show'.

Options:
    -h, --help      Show this help message

Examples:
    iprule          # Show routing rules
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the iprule command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Default routing policy rules (most systems have these)
            self.console.print("0:\tfrom all lookup local")
            self.console.print("32766:\tfrom all lookup main")
            self.console.print("32767:\tfrom all lookup default")

            # Try to read additional rules from /etc/iproute2/rt_tables or similar
            try:
                rt_tables = safe_read_file(
                    client, "/etc/iproute2/rt_tables", self.shell
                )
                if rt_tables:
                    # Parse custom routing tables
                    custom_tables = []
                    for line in rt_tables.split("\n"):
                        line = line.strip()
                        if line and not line.startswith("#"):
                            parts = line.split()
                            if len(parts) >= 2:
                                table_id = parts[0]
                                table_name = parts[1]
                                if table_name not in ["local", "main", "default"]:
                                    custom_tables.append((table_id, table_name))

                    # Display custom table rules (simplified)
                    for table_id, table_name in custom_tables:
                        if table_id.isdigit() and int(table_id) < 32766:
                            self.console.print(
                                f"{table_id}:\tfrom all lookup {table_name}"
                            )
            except Exception:  # noqa: S110
                # Broad exception needed for network configuration probing
                pass

            return 0

        except Exception as e:
            self.console.print(f"[red]iprule: {e}[/red]")
            return 1
