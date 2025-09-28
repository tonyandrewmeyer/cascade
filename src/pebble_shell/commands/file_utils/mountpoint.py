"""Implementation of MountpointCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.proc_reader import read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class MountpointCommand(Command):
    """Implementation of mountpoint command."""

    name = "mountpoint"
    help = "Check if directory is a mountpoint"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Check if directory is a mountpoint.

Usage: mountpoint [OPTIONS] DIRECTORY

Description:
    Check whether the given directory is a mountpoint.

Options:
    -q, --quiet     Be quiet - don't print anything
    -d, --fs-devno  Print the major/minor device number of filesystem
    -x, --devno     Print the major/minor device number of block device
    -h, --help      Show this help message

Exit codes:
    0 - Directory is a mountpoint
    1 - Directory is not a mountpoint

Examples:
    mountpoint /mnt         # Check if /mnt is a mountpoint
    mountpoint -q /proc     # Quiet check
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the mountpoint command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "q": bool,  # quiet
                "quiet": bool,  # quiet
                "d": bool,  # filesystem device number
                "fs-devno": bool,  # filesystem device number
                "x": bool,  # block device number
                "devno": bool,  # block device number
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        quiet = flags.get("q", False) or flags.get("quiet", False)
        show_fs_devno = flags.get("d", False) or flags.get("fs-devno", False)
        show_devno = flags.get("x", False) or flags.get("devno", False)

        if len(positional_args) != 1:
            if not quiet:
                self.console.print(
                    "[red]" + "mountpoint: exactly one directory required" + "[/red]"
                )
            return 1

        directory = positional_args[0]

        try:
            is_mountpoint = self._is_mountpoint(client, directory)

            if is_mountpoint:
                if not quiet:
                    if show_fs_devno or show_devno:
                        # Try to get device numbers
                        devno = self._get_device_number(client, directory)
                        if devno:
                            self.console.print(
                                f"{directory} is a mountpoint (device: {devno})"
                            )
                        else:
                            self.console.print(f"{directory} is a mountpoint")
                    else:
                        self.console.print(f"{directory} is a mountpoint")
                return 0
            else:
                if not quiet:
                    self.console.print(f"{directory} is not a mountpoint")
                return 1

        except Exception as e:
            if not quiet:
                self.console.print("[red]" + f"mountpoint: {e}" + "[/red]")
            return 1

    def _is_mountpoint(self, client: ClientType, directory: str) -> bool:
        """Check if directory is a mountpoint by examining /proc/mounts."""
        try:
            if not directory.startswith("/"):
                directory = "/" + directory
            directory = directory.rstrip("/")
            if not directory:
                directory = "/"

            mounts_content = read_proc_file(client, "/proc/mounts")
            for line in mounts_content.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    mount_point = parts[1]
                    if mount_point == directory:
                        return True

        except ops.pebble.PathError:
            pass

        return False

    def _get_device_number(self, client: ClientType, directory: str) -> str | None:
        """Get device number for the filesystem at the given directory."""
        try:
            mounts_content = read_proc_file(client, "/proc/mounts")
            for line in mounts_content.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    device = parts[0]
                    mount_point = parts[1]
                    if mount_point == directory:
                        # Try to get major:minor from device
                        return device

        except ops.pebble.PathError:
            pass

        return None
