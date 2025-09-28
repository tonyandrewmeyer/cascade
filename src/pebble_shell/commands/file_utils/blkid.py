"""Implementation of BlkidCommand."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from ...utils.proc_reader import read_proc_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class BlkidCommand(Command):
    """Implementation of blkid command."""

    name = "blkid"
    help = "Locate/print block device attributes"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Locate/print block device attributes.

Usage: blkid [OPTIONS] [DEVICE...]

Description:
    Display block device attributes like UUID, LABEL, TYPE, etc.
    If no devices specified, shows all available devices.

Options:
    -L LABEL        Find device with specified label
    -U UUID         Find device with specified UUID
    -s TAG          Show only specified tag
    -o FORMAT       Output format (value, device, list, full)
    -h, --help      Show this help message

Examples:
    blkid                   # Show all devices
    blkid /dev/sda1         # Show specific device
    blkid -L "mydata"       # Find device with label "mydata"
    blkid -U "1234-5678"    # Find device with UUID
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the blkid command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "L": str,  # label
                "U": str,  # uuid
                "s": str,  # tag
                "o": str,  # output format
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        label_search = flags.get("L")
        uuid_search = flags.get("U")
        tag_filter = flags.get("s")
        output_format = flags.get("o", "full")
        devices = positional_args

        try:
            device_info = {}

            # If specific devices requested, check those
            if devices:
                for device in devices:
                    info = self._get_device_info(client, device)
                    if info:
                        device_info[device] = info
            else:
                # Scan common locations for devices
                device_info = self._scan_all_devices(client)

            # Filter by label or UUID if requested
            if label_search:
                filtered = {}
                for dev, info in device_info.items():
                    if info.get("LABEL") == label_search:
                        filtered[dev] = info
                device_info = filtered

            if uuid_search:
                filtered = {}
                for dev, info in device_info.items():
                    if info.get("UUID") == uuid_search:
                        filtered[dev] = info
                device_info = filtered

            # Display results
            if not device_info:
                return 1  # No devices found

            for device, info in device_info.items():
                self._display_device_info(device, info, tag_filter, output_format)

            return 0

        except Exception as e:
            self.console.print(f"[red]blkid: {e}[/red]")
            return 1

    def _get_device_info(self, client: ClientType, device: str) -> dict[str, str]:
        """Get information about a specific device."""
        info = {}

        try:
            # Try to read filesystem type and other info from various sources
            device_name = os.path.basename(device)

            # Check /sys/block or /sys/class/block
            sys_paths = [
                f"/sys/class/block/{device_name}",
                f"/sys/block/{device_name}",
            ]

            for sys_path in sys_paths:
                try:
                    # Try to read various attributes
                    for attr in ["uuid", "label", "type"]:
                        try:
                            content = safe_read_file(
                                client, f"{sys_path}/{attr}", self.shell
                            )
                            value = content.decode("utf-8").strip() if content else None
                            if value:
                                info[attr.upper()] = value
                        except ops.pebble.PathError:  # noqa: PERF203  # needed for device attribute probing
                            continue
                    break
                except ops.pebble.PathError:
                    continue

            # Try to read from /dev/disk/by-uuid and /dev/disk/by-label
            mounts_content = read_proc_file(client, "/proc/mounts")
            for line in mounts_content.splitlines():
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0] == device:
                    info["TYPE"] = parts[2]
                    break

            # Try to get UUID and LABEL from /dev/disk/by-*
            # TODO: Implement this.

        except Exception:  # noqa: S110
            # Broad exception needed for device discovery which can fail in many ways
            pass

        return info

    def _scan_all_devices(self, client: ClientType) -> dict[str, dict[str, str]]:
        """Scan for all available block devices."""
        devices = {}

        try:
            # Read /proc/partitions to find devices
            partitions_content = read_proc_file(client, "/proc/partitions")
            for line in partitions_content.splitlines():
                parts = line.strip().split()
                if len(parts) >= 4 and parts[0].isdigit():
                    device_name = parts[3]
                    device_path = f"/dev/{device_name}"
                    info = self._get_device_info(client, device_path)
                    if info:
                        devices[device_path] = info
                    else:
                        # Even if no detailed info, show the device exists
                        devices[device_path] = {}
        except ops.pebble.PathError:
            # /proc/partitions may not exist in some containers
            pass

        return devices

    def _display_device_info(
        self, device: str, info: dict[str, str], tag_filter: str, output_format: str
    ):
        """Display device information in the requested format."""
        if tag_filter and tag_filter in info:
            # Show only specific tag
            if output_format == "value":
                self.console.print(info[tag_filter])
            else:
                self.console.print(f'{device}: {tag_filter}="{info[tag_filter]}"')
        elif tag_filter:
            # Tag requested but not found - show nothing
            pass
        else:
            # Show all info
            if output_format == "device":
                self.console.print(device)
            elif output_format == "list":
                attrs = " ".join(f'{k}="{v}"' for k, v in info.items())
                self.console.print(f"{device} {attrs}")
            else:  # full format
                if info:
                    attrs = " ".join(f'{k}="{v}"' for k, v in info.items())
                    self.console.print(f"{device}: {attrs}")
                else:
                    self.console.print(device)
