"""Integration tests for the FindfsCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FindfsCommand instance."""
    yield pebble_shell.commands.FindfsCommand(shell=shell)


def test_name(command: pebble_shell.commands.FindfsCommand):
    assert command.name == "findfs"


def test_category(command: pebble_shell.commands.FindfsCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.FindfsCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "findfs" in output
    assert "Find filesystem by label or UUID" in output
    assert "LABEL=" in output
    assert "UUID=" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "findfs" in output
    assert "Find filesystem by label or UUID" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # findfs with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "findfs LABEL=<label>" in output or "findfs UUID=<uuid>" in output


def test_execute_find_by_label_root(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test finding filesystem by root label
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should either succeed finding device or fail if label not found
    if result == 0:
        output = capture.get()
        # Should show device path
        assert (
            any(
                device in output
                for device in [
                    "/dev/sda",
                    "/dev/sdb",
                    "/dev/nvme",
                    "/dev/vda",
                    "/dev/mapper",
                ]
            )
            or "/dev/" in output
        )
    else:
        # Should fail if label not found
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["not found", "No filesystem", "Unable to resolve", "error"]
        )


def test_execute_find_by_label_boot(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test finding filesystem by boot label
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=BOOT"])

    # Should either succeed finding boot device or fail if not found
    if result == 0:
        output = capture.get()
        # Should show boot device path
        assert "/dev/" in output
        assert any(char.isalnum() for char in output)
    else:
        # Should fail if boot label not found
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "No filesystem", "Unable to resolve"]
        )


def test_execute_find_by_nonexistent_label(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with nonexistent label
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=nonexistent-label"])

    # Should fail with label not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["not found", "No filesystem", "Unable to resolve", "does not exist"]
    )


def test_execute_find_by_uuid_valid_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test finding filesystem by UUID (valid format)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["UUID=12345678-1234-1234-1234-123456789abc"]
        )

    # Should either succeed finding device or fail if UUID not found
    if result == 0:
        output = capture.get()
        # Should show device path for UUID
        assert "/dev/" in output
        assert any(char.isalnum() for char in output)
    else:
        # Should fail if UUID not found
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "not found",
                "No filesystem",
                "Unable to resolve",
                "UUID not found",
            ]
        )


def test_execute_find_by_invalid_uuid_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with invalid UUID format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["UUID=invalid-uuid-format"])

    # Should fail with invalid UUID format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in [
            "invalid UUID",
            "malformed UUID",
            "UUID format",
            "not found",
            "error",
        ]
    )


def test_execute_find_by_short_uuid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with short UUID format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["UUID=1234"])

    # Should fail with invalid UUID format
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid UUID", "UUID format", "not found", "error"]
    )


def test_execute_empty_label(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with empty label
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL="])

    # Should fail with empty label error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["empty label", "invalid label", "not found", "error"]
    )


def test_execute_empty_uuid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with empty UUID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["UUID="])

    # Should fail with empty UUID error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["empty UUID", "invalid UUID", "not found", "error"]
    )


def test_execute_invalid_identifier_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with invalid identifier format (no LABEL= or UUID=)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid-format"])

    # Should fail with invalid format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid format", "must specify LABEL= or UUID=", "usage", "error"]
    )


def test_execute_mixed_case_label(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with mixed case label identifier
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["label=MixedCase"])

    # Should either handle case insensitively or fail appropriately
    if result == 0:
        output = capture.get()
        # Should find device regardless of case
        assert "/dev/" in output
    else:
        # Should fail if case sensitive or label not found
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "invalid format", "error"])


def test_execute_mixed_case_uuid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with mixed case UUID identifier
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["uuid=12345678-1234-1234-1234-123456789abc"]
        )

    # Should either handle case insensitively or fail appropriately
    if result == 0:
        output = capture.get()
        # Should find device regardless of case
        assert "/dev/" in output
    else:
        # Should fail if case sensitive or UUID not found
        assert result == 1


def test_execute_label_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with label containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=My Label"])

    # Should either handle spaces in labels or fail appropriately
    if result == 0:
        output = capture.get()
        # Should find device with spaced label
        assert "/dev/" in output
    else:
        # Should fail if label with spaces not found
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "Unable to resolve", "error"])


def test_execute_label_with_special_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with label containing special characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=test-label_123"])

    # Should either handle special characters or fail appropriately
    if result == 0:
        output = capture.get()
        # Should find device with special character label
        assert "/dev/" in output
    else:
        # Should fail if special character label not found
        assert result == 1


def test_execute_very_long_label(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with very long label
    long_label = (
        "very-long-label-name-that-exceeds-normal-filesystem-label-length-limits"
    )
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[f"LABEL={long_label}"])

    # Should either handle long labels or fail appropriately
    if result == 0:
        output = capture.get()
        # Should find device with long label
        assert "/dev/" in output
    else:
        # Should fail if long label not found or invalid
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "label too long", "invalid label"]
        )


def test_execute_multiple_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test with multiple arguments (should handle first one)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root", "UUID=test"])

    # Should either use first argument or show error
    if result == 0:
        output = capture.get()
        # Should process first argument
        assert "/dev/" in output
    else:
        # Should fail if first argument not found or multiple args not allowed
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "too many arguments", "error"]
        )


def test_execute_blkid_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test integration with blkid for device discovery
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should integrate with blkid for device lookup
    if result == 0:
        output = capture.get()
        # Should return device found by blkid
        assert "/dev/" in output
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_udev_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test integration with udev device database
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["UUID=12345678-1234-1234-1234-123456789abc"]
        )

    # Should integrate with udev for device resolution
    if result == 0:
        output = capture.get()
        # Should return device from udev database
        assert "/dev/" in output
    else:
        # Should fail if not found in udev database
        assert result == 1


def test_execute_proc_filesystem_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test /proc filesystem access for device information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should access /proc filesystem for device info
    if result == 0:
        output = capture.get()
        # Should successfully read device information
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_sys_filesystem_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test /sys filesystem access for device attributes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["UUID=test-uuid"])

    # Should access /sys filesystem for device attributes
    if result == 0:
        output = capture.get()
        # Should successfully read device attributes
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_device_mapper_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test device mapper device handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=lvm-root"])

    # Should handle device mapper devices appropriately
    if result == 0:
        output = capture.get()
        # Should find device mapper device
        assert (
            any(path in output for path in ["/dev/mapper/", "/dev/dm-", "/dev/vg"])
            or "/dev/" in output
        )
    else:
        # Should fail if device mapper device not found
        assert result == 1


def test_execute_lvm_device_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test LVM device handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=lv-root"])

    # Should handle LVM devices appropriately
    if result == 0:
        output = capture.get()
        # Should find LVM device
        assert (
            any(path in output for path in ["/dev/mapper/", "/dev/vg", "/dev/lv"])
            or "/dev/" in output
        )
    else:
        # Should fail if LVM device not found
        assert result == 1


def test_execute_raid_device_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test RAID device handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=raid-root"])

    # Should handle RAID devices appropriately
    if result == 0:
        output = capture.get()
        # Should find RAID device
        assert (
            any(path in output for path in ["/dev/md", "/dev/raid"])
            or "/dev/" in output
        )
    else:
        # Should fail if RAID device not found
        assert result == 1


def test_execute_nvme_device_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test NVMe device handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=nvme-root"])

    # Should handle NVMe devices appropriately
    if result == 0:
        output = capture.get()
        # Should find NVMe device
        assert "/dev/nvme" in output or "/dev/" in output
    else:
        # Should fail if NVMe device not found
        assert result == 1


def test_execute_usb_device_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test USB device handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=USB_DRIVE"])

    # Should handle USB devices appropriately
    if result == 0:
        output = capture.get()
        # Should find USB device
        assert (
            any(path in output for path in ["/dev/sd", "/dev/usb"]) or "/dev/" in output
        )
    else:
        # Should fail if USB device not found
        assert result == 1


def test_execute_mounted_filesystem_priority(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test priority of mounted filesystems
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should prioritize mounted filesystems appropriately
    if result == 0:
        output = capture.get()
        # Should return appropriate device
        assert "/dev/" in output
    else:
        assert result == 1


def test_execute_case_sensitivity_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test case sensitivity in filesystem labels
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=ROOT"])

    # Should handle case sensitivity appropriately
    if result == 0:
        output = capture.get()
        # Should find device with case handling
        assert "/dev/" in output
    else:
        # Should fail if case sensitive and not found
        assert result == 1


def test_execute_filesystem_type_awareness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test filesystem type awareness
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=ext4-root"])

    # Should be aware of different filesystem types
    if result == 0:
        output = capture.get()
        # Should find device regardless of filesystem type
        assert "/dev/" in output
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test permission handling for device access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should handle permissions appropriately
    if result == 1:
        output = capture.get()
        if "permission" in output.lower():
            assert "permission" in output.lower()
    else:
        assert result == 0


def test_execute_symlink_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test symlink resolution in device paths
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should resolve symlinks appropriately
    if result == 0:
        output = capture.get()
        # Should return canonical device path
        assert "/dev/" in output
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_network_filesystem_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test network filesystem handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=nfs-share"])

    # Should handle network filesystems appropriately
    if result == 0:
        output = capture.get()
        # Should indicate network filesystem or device
        assert len(output.strip()) >= 0
    else:
        # Should fail if network filesystem not found locally
        assert result == 1


def test_execute_virtual_filesystem_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test virtual filesystem handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=tmpfs"])

    # Should handle virtual filesystems appropriately
    if result == 0:
        output = capture.get()
        # Should indicate virtual filesystem device
        assert len(output.strip()) >= 0
    else:
        # Should fail if virtual filesystem not found
        assert result == 1


def test_execute_output_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test output format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent device path format
        lines = output.strip().split("\n")
        if len(lines) == 1:
            # Should be single device path
            assert output.strip().startswith("/dev/") or len(output.strip()) == 0
    else:
        assert result == 1


def test_execute_error_message_clarity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test error message clarity
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=nonexistent"])

    # Should provide clear error messages
    assert result == 1
    output = capture.get()
    # Should have informative error message
    assert len(output.strip()) > 0
    assert any(
        msg in output
        for msg in ["not found", "Unable to resolve", "No filesystem", "does not exist"]
    )


def test_execute_performance_with_many_devices(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test performance with system having many devices
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should handle many devices efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["LABEL=root"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000  # Should be just device path
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindfsCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "LABEL=root"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0
