"""Implementation of VolnameCommand."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file
from ...utils.proc_reader import read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class VolnameCommand(Command):
    """Implementation of volname command."""

    name = "volname"
    help = "Display volume name"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Display volume name.

Usage: volname [DEVICE]

Description:
    Display the volume name of a filesystem.
    If no device is specified, tries to determine the root filesystem.

Examples:
    volname             # Volume name of root filesystem
    volname /dev/sda1   # Volume name of specific device
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the volname command."""
        if handle_help_flag(self, args):
            return 0

        device = args[0] if args else "/"

        try:
            # Try to get volume information from various sources
            volume_name = ""

            # Check if it's a device file
            if device.startswith("/dev/"):
                # Try to read filesystem label
                label_files = [
                    f"/sys/class/block/{os.path.basename(device)}/device/label",
                    f"/sys/block/{os.path.basename(device)}/device/label",
                ]

                for label_file in label_files:
                    content = safe_read_file(client, label_file, self.shell)
                    if content:
                        volume_name = content.strip()
                        if volume_name:
                            break

                # Try blkid approach via /proc/mounts
                if not volume_name:
                    mounts_content = read_proc_file(client, "/proc/mounts")
                    for line in mounts_content.splitlines():
                        parts = line.strip().split()
                        if len(parts) >= 2 and parts[0] == device:
                            # Found the device, but we can't easily get label from here
                            break
            else:
                # It's a path, try to find the filesystem it's on
                try:
                    mounts_content = read_proc_file(client, "/proc/mounts")
                    mounts = []
                    for line in mounts_content.splitlines():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            mounts.append((parts[1], parts[0]))  # (mountpoint, device)

                    # Find the mount point that contains our path
                    device_path = device if device.startswith("/") else "/"
                    best_match = ""
                    best_device = ""

                    for mount_point, mount_device in mounts:
                        if device_path.startswith(mount_point) and len(
                            mount_point
                        ) > len(best_match):
                            best_match = mount_point
                            best_device = mount_device

                    if best_device and best_device.startswith("/dev/"):
                        device_name = os.path.basename(best_device)
                        label_files = [
                            f"/sys/class/block/{device_name}/label",
                            f"/sys/block/{device_name}/label",
                        ]

                        for label_file in label_files:
                            try:
                                content = safe_read_file(client, label_file, self.shell)
                                volume_name = (
                                    content.decode("utf-8").strip() if content else None
                                )
                                if volume_name:
                                    break
                            except ops.pebble.PathError:
                                continue

                except ops.pebble.PathError:
                    pass

            # Output result
            if volume_name:
                self.console.print(volume_name)
            else:
                # No volume name found, but this isn't necessarily an error
                # Some filesystems don't have labels
                pass

            return 0

        except Exception as e:
            self.console.print("[red]" + f"volname: {e}" + "[/red]")
            return 1
