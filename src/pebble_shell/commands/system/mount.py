"""Implementation of MountCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import parse_proc_mounts_file
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class MountCommand(Command):
    """Show mounted filesystems."""

    name = "mount"
    help = "Show mounted filesystems"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute mount command."""
        if handle_help_flag(self, args):
            return 0
        try:
            mounts = parse_proc_mounts_file(client)

            table = create_enhanced_table()
            table.add_column("Device", style="cyan", no_wrap=True)
            table.add_column("Mount Point", style="green", no_wrap=True)
            table.add_column("Type", style="yellow", no_wrap=True)
            table.add_column("Options", style="blue", no_wrap=False)

            for mount_info in mounts:
                device = mount_info["device"]
                mount_point = mount_info["mountpoint"]
                fs_type = mount_info["fstype"]
                options = mount_info["options"]

                # Color code different filesystem types
                if fs_type in ["ext4", "xfs", "btrfs"]:
                    fs_type_colored = f"[green]{fs_type}[/green]"
                elif fs_type in ["proc", "sysfs", "tmpfs"]:
                    fs_type_colored = f"[blue]{fs_type}[/blue]"
                elif fs_type in ["devpts", "devtmpfs"]:
                    fs_type_colored = f"[yellow]{fs_type}[/yellow]"
                else:
                    fs_type_colored = fs_type

                table.add_row(device, mount_point, fs_type_colored, options)

            self.console.print(table.build())

        except Exception as e:
            self.console.print(f"Error reading mount information: {e}")
            return 1

        return 0
