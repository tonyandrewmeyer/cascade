"""Implementation of FindfsCommand."""

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


class FindfsCommand(Command):
    """Implementation of findfs command."""

    name = "findfs"
    help = "Find filesystem by label or UUID"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Find filesystem by label or UUID.

Usage: findfs LABEL=label | UUID=uuid

Description:
    Find the device that contains a filesystem with the specified
    label or UUID and print the device name.

Examples:
    findfs LABEL=boot       # Find device with label "boot"
    findfs UUID=1234-5678   # Find device with UUID "1234-5678"
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the findfs command."""
        if handle_help_flag(self, args):
            return 0

        if len(args) != 1:
            self.console.print("[red]" + "findfs: missing operand" + "[/red]")
            return 1

        try:
            search_spec = args[0]

            if search_spec.startswith("LABEL="):
                label = search_spec[6:]
                device = self._find_by_label(client, label)
            elif search_spec.startswith("UUID="):
                uuid = search_spec[5:]
                device = self._find_by_uuid(client, uuid)
            else:
                self.console.print(
                    "[red]" + "findfs: invalid argument format" + "[/red]"
                )
                return 1

            if device:
                self.console.print(device)
                return 0
            else:
                return 1  # Not found

        except Exception as e:
            self.console.print("[red]" + f"findfs: {e}" + "[/red]")
            return 1

    def _find_by_label(self, client: ClientType, label: str) -> str | None:
        """Find device by filesystem label."""
        try:
            # Try /dev/disk/by-label/ first (if available)
            # /dev/disk/by-label/{label} would be a symlink, but we can't easily resolve it
            # So we'll search through devices manually

            # Search through /proc/partitions and check each device
            try:
                partitions_content = read_proc_file(client, "/proc/partitions")
                for line in partitions_content.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[0].isdigit():
                        device_name = parts[3]
                        device_path = f"/dev/{device_name}"

                        # Check if this device has the label we're looking for
                        if self._check_device_label(client, device_path, label):
                            return device_path
            except ops.pebble.PathError:
                pass

        except Exception:  # noqa: S110
            # Broad exception needed for filesystem discovery which can fail in many ways
            pass

        return None

    def _find_by_uuid(self, client: ClientType, uuid: str) -> str | None:
        """Find device by filesystem UUID."""
        try:
            # Search through /proc/partitions and check each device
            try:
                partitions_content = read_proc_file(client, "/proc/partitions")
                for line in partitions_content.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[0].isdigit():
                        device_name = parts[3]
                        device_path = f"/dev/{device_name}"

                        # Check if this device has the UUID we're looking for
                        if self._check_device_uuid(client, device_path, uuid):
                            return device_path
            except ops.pebble.PathError:
                pass

        except Exception:  # noqa: S110
            # Broad exception needed for filesystem discovery which can fail in many ways
            pass

        return None

    def _check_device_label(self, client: ClientType, device: str, label: str) -> bool:
        """Check if device has the specified label."""
        try:
            device_name = os.path.basename(device)
            label_files = [
                f"/sys/class/block/{device_name}/label",
                f"/sys/block/{device_name}/label",
            ]

            for label_file in label_files:
                try:
                    content = safe_read_file(client, label_file, self.shell)
                    device_label = content.decode("utf-8").strip() if content else None
                    if device_label == label:
                        return True
                except ops.pebble.PathError:  # noqa: PERF203  # needed for device probing
                    continue

        except Exception:  # noqa: S110
            # Broad exception needed for device probing which can fail in many ways
            pass

        return False

    def _check_device_uuid(self, client: ClientType, device: str, uuid: str) -> bool:
        """Check if device has the specified UUID."""
        try:
            device_name = os.path.basename(device)
            uuid_files = [
                f"/sys/class/block/{device_name}/uuid",
                f"/sys/block/{device_name}/uuid",
            ]

            for uuid_file in uuid_files:
                try:
                    content = safe_read_file(client, uuid_file, self.shell)
                    device_uuid = content.decode("utf-8").strip() if content else None
                    if device_uuid == uuid:
                        return True
                except ops.pebble.PathError:  # noqa: PERF203  # needed for device probing
                    continue

        except Exception:  # noqa: S110
            # Broad exception needed for device probing which can fail in many ways
            pass

        return False
