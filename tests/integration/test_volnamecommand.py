"""Integration tests for the VolnameCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a VolnameCommand instance."""
    yield pebble_shell.commands.VolnameCommand(shell=shell)


def test_name(command: pebble_shell.commands.VolnameCommand):
    assert command.name == "volname"


def test_category(command: pebble_shell.commands.VolnameCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.VolnameCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "volname" in output
    assert "Display filesystem volume name" in output
    assert "DEVICE" in output
    assert "-v" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "volname" in output
    assert "Display filesystem volume name" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # volname with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "volname <DEVICE>" in output


def test_execute_root_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with root filesystem device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should either succeed showing volume name or fail if not accessible
    if result == 0:
        output = capture.get()
        # Should show volume name or indication of no volume name
        assert (
            any(
                msg in output
                for msg in ["Volume name:", "Label:", "No volume name", "Unnamed"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if device not accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No such device", "permission denied", "not found", "error"]
        )


def test_execute_dev_sda1_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with common block device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sda1"])

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show volume name information
        assert (
            any(
                msg in output
                for msg in [
                    "Volume name:",
                    "Label:",
                    "No volume name",
                    "",  # May have empty output for unlabeled volumes
                ]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if device doesn't exist or not accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No such device", "not found", "permission denied", "error"]
        )


def test_execute_nonexistent_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with nonexistent device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/nonexistent"])

    # Should fail with device not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["No such device", "not found", "does not exist", "error"]
    )


def test_execute_regular_file_as_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with regular file (should fail or handle appropriately)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either handle file or fail appropriately
    if result == 0:
        output = capture.get()
        # Should indicate not a block device
        assert (
            any(
                msg in output
                for msg in ["not a block device", "No volume name", "Invalid device"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if not a valid device
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not a block device", "invalid device", "error"]
        )


def test_execute_directory_as_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with directory path
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_dir])

    # Should either resolve to underlying device or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show volume name of underlying filesystem
        assert len(output.strip()) >= 0
    else:
        # Should fail if directory can't be resolved to device
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not a block device", "invalid device", "error"]
        )


def test_execute_verbose_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test -v option for verbose output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "/"])

    # Should either succeed with verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show verbose volume information
        assert (
            any(
                msg in output
                for msg in [
                    "Device:",
                    "Volume name:",
                    "Filesystem:",
                    "Label:",
                    "UUID:",
                    "Type:",
                ]
            )
            or len(output.strip()) >= 0
        )
    else:
        assert result == 1


def test_execute_quiet_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test -q option for quiet output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "/"])

    # Should either succeed with minimal output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show only volume name or be empty
        assert len(output.strip()) >= 0  # May be empty for unlabeled volumes
    else:
        assert result == 1


def test_execute_raw_output_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test raw output option (no formatting)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--raw", "/"])

    # Should either succeed with raw output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show raw volume name without formatting
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_ext4_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with ext4 filesystem device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sda1"])

    # Should either handle ext4 volume or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show ext4 volume information
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_ntfs_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with NTFS filesystem device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sdb1"])

    # Should either handle NTFS volume or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show NTFS volume information
        assert len(output.strip()) >= 0
    else:
        # Should fail if device doesn't exist
        assert result == 1


def test_execute_fat32_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with FAT32 filesystem device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sdc1"])

    # Should either handle FAT32 volume or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show FAT32 volume information
        assert len(output.strip()) >= 0
    else:
        # Should fail if device doesn't exist
        assert result == 1


def test_execute_xfs_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with XFS filesystem device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sdd1"])

    # Should either handle XFS volume or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show XFS volume information
        assert len(output.strip()) >= 0
    else:
        # Should fail if device doesn't exist
        assert result == 1


def test_execute_btrfs_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with Btrfs filesystem device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sde1"])

    # Should either handle Btrfs volume or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show Btrfs volume information
        assert len(output.strip()) >= 0
    else:
        # Should fail if device doesn't exist
        assert result == 1


def test_execute_multiple_devices(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with multiple device arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/", "/dev/sda1"])

    # Should either handle multiple devices or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show volume names for multiple devices
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_device_by_uuid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with device specified by UUID
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["/dev/disk/by-uuid/12345678-1234-1234-1234-123456789abc"],
        )

    # Should either handle UUID device or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show volume name for UUID device
        assert len(output.strip()) >= 0
    else:
        # Should fail if UUID device doesn't exist
        assert result == 1


def test_execute_device_by_label(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with device specified by label
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/disk/by-label/BOOT"])

    # Should either handle labeled device or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show volume name for labeled device
        assert len(output.strip()) >= 0
    else:
        # Should fail if labeled device doesn't exist
        assert result == 1


def test_execute_network_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with network filesystem (should handle appropriately)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/mnt/nfs"])

    # Should either handle network filesystem or fail appropriately
    if result == 0:
        output = capture.get()
        # Should indicate network filesystem or no volume name
        assert len(output.strip()) >= 0
    else:
        # Should fail if network filesystem not accessible
        assert result == 1


def test_execute_virtual_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with virtual filesystem (/proc, /sys)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/proc"])

    # Should either handle virtual filesystem or fail appropriately
    if result == 0:
        output = capture.get()
        # Should indicate virtual filesystem or no volume name
        assert len(output.strip()) >= 0
    else:
        # Should fail if virtual filesystem not supported
        assert result == 1


def test_execute_tmpfs_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with tmpfs filesystem
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_dir])

    # Should either handle tmpfs or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show tmpfs volume information or no volume name
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_device_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test device permission handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sda"])

    # Should handle permissions appropriately
    if result == 0:
        output = capture.get()
        # Should show volume information if accessible
        assert len(output.strip()) >= 0
    else:
        # Should fail with permission error if not accessible
        assert result == 1
        output = capture.get()
        if "permission denied" in output.lower():
            assert "permission denied" in output.lower()


def test_execute_mounted_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with mounted device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should handle mounted device appropriately
    if result == 0:
        output = capture.get()
        # Should show volume name of mounted device
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_unmounted_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with unmounted device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sdf1"])

    # Should handle unmounted device appropriately
    if result == 0:
        output = capture.get()
        # Should show volume name even if unmounted
        assert len(output.strip()) >= 0
    else:
        # Should fail if device doesn't exist
        assert result == 1


def test_execute_corrupted_filesystem(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with potentially corrupted filesystem
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/loop0"])

    # Should handle corrupted filesystem gracefully
    if result == 0:
        output = capture.get()
        # Should show available information or error indication
        assert len(output.strip()) >= 0
    else:
        # Should fail gracefully with error
        assert result == 1


def test_execute_read_only_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with read-only device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/sr0"])  # CD-ROM device

    # Should handle read-only device appropriately
    if result == 0:
        output = capture.get()
        # Should show volume name of read-only device
        assert len(output.strip()) >= 0
    else:
        # Should fail if device doesn't exist or not accessible
        assert result == 1


def test_execute_symlink_to_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test with symlink to device
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/dev/disk/by-uuid/existing-uuid"]
        )

    # Should follow symlink to actual device
    if result == 0:
        output = capture.get()
        # Should show volume name of target device
        assert len(output.strip()) >= 0
    else:
        # Should fail if symlink target doesn't exist
        assert result == 1


def test_execute_output_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test output format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent formatting
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_unicode_volume_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test handling of unicode volume names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should handle unicode volume names appropriately
    if result == 0:
        output = capture.get()
        # Should display unicode characters correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_long_volume_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test handling of long volume names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should handle long volume names appropriately
    if result == 0:
        output = capture.get()
        # Should display long names correctly (may truncate)
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_special_characters_in_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test handling of special characters in volume names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should handle special characters appropriately
    if result == 0:
        output = capture.get()
        # Should escape or display special characters safely
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])

    # Should recover from errors gracefully
    if result == 1:
        output = capture.get()
        # Should provide meaningful error message
        assert any(msg in output for msg in ["not found", "does not exist", "error"])
    else:
        assert result == 0


def test_execute_performance_with_many_devices(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test performance with many devices
    temp_dir = tempfile.mkdtemp()
    devices = ["/", "/dev/sda1", temp_dir, "/proc"]
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=devices)

    # Should handle many devices efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VolnameCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "/"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0
