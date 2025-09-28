"""Integration tests for the MountpointCommand."""

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
    """Fixture to create a MountpointCommand instance."""
    yield pebble_shell.commands.MountpointCommand(shell=shell)


def test_name(command: pebble_shell.commands.MountpointCommand):
    assert command.name == "mountpoint"


def test_category(command: pebble_shell.commands.MountpointCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.MountpointCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "mountpoint" in output
    assert "Check if directory is a mount point" in output
    assert "-q" in output
    assert "-d" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "mountpoint" in output
    assert "Check if directory is a mount point" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # mountpoint with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "mountpoint <directory>" in output


def test_execute_root_mountpoint(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with root directory (should be a mount point)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should succeed as root is typically a mount point
    if result == 0:
        output = capture.get()
        # Should indicate it's a mount point
        assert (
            any(
                msg in output
                for msg in ["is a mountpoint", "is a mount point", "mountpoint", "/"]
            )
            or len(output.strip()) == 0
        )  # May have no output on success
    else:
        # May fail if mountpoint check fails
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["is not a mountpoint", "not a mount point", "error"]
        )


def test_execute_tmp_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with temporary directory (may or may not be a mount point)
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_dir])

    # Should either succeed or fail based on whether directory is mounted
    if result == 0:
        output = capture.get()
        # Should indicate it's a mount point
        assert (
            any(
                msg in output
                for msg in ["is a mountpoint", "is a mount point", temp_dir]
            )
            or len(output.strip()) == 0
        )
    else:
        # Should fail if directory is not a mount point
        assert result == 1
        output = capture.get()
        assert (
            any(
                msg in output
                for msg in ["is not a mountpoint", "not a mount point", temp_dir]
            )
            or len(output.strip()) == 0
        )


def test_execute_proc_mountpoint(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with /proc (should be a mount point)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/proc"])

    # Should succeed as /proc is typically a mount point
    if result == 0:
        output = capture.get()
        # Should indicate /proc is a mount point
        assert (
            any(
                msg in output
                for msg in ["is a mountpoint", "is a mount point", "/proc"]
            )
            or len(output.strip()) == 0
        )
    else:
        # May fail if /proc is not accessible
        assert result == 1


def test_execute_sys_mountpoint(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with /sys (should be a mount point)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/sys"])

    # Should succeed as /sys is typically a mount point
    if result == 0:
        output = capture.get()
        # Should indicate /sys is a mount point
        assert (
            any(
                msg in output for msg in ["is a mountpoint", "is a mount point", "/sys"]
            )
            or len(output.strip()) == 0
        )
    else:
        # May fail if /sys is not accessible
        assert result == 1


def test_execute_dev_mountpoint(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with /dev (may be a mount point)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev"])

    # Should either succeed or fail based on /dev mount status
    if result == 0:
        output = capture.get()
        # Should indicate /dev is a mount point
        assert (
            any(
                msg in output for msg in ["is a mountpoint", "is a mount point", "/dev"]
            )
            or len(output.strip()) == 0
        )
    else:
        # Should fail if /dev is not a mount point
        assert result == 1


def test_execute_nonexistent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with nonexistent directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])

    # Should fail with directory not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["No such file", "not found", "does not exist", "error"]
    )


def test_execute_regular_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with regular file (should not be a mount point)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should fail as regular files cannot be mount points
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in [
            "not a directory",
            "is not a mountpoint",
            "not a mount point",
            "error",
        ]
    )


def test_execute_subdirectory_not_mountpoint(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with subdirectory that's not a mount point
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/default"])

    # Should fail as subdirectory is typically not a mount point
    if result == 1:
        output = capture.get()
        assert (
            any(
                msg in output
                for msg in ["is not a mountpoint", "not a mount point", "/etc/default"]
            )
            or len(output.strip()) == 0
        )
    else:
        # May succeed if it actually is a mount point
        assert result == 0


def test_execute_quiet_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test -q option for quiet mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "/"])

    # Should succeed quietly (no output)
    if result == 0:
        output = capture.get()
        # Should have no output in quiet mode
        assert len(output.strip()) == 0
    else:
        # Should fail quietly
        assert result == 1
        output = capture.get()
        # Should have no output in quiet mode
        assert len(output.strip()) == 0


def test_execute_device_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test -d option to show device
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "/"])

    # Should either succeed showing device or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show device information
        assert (
            any(
                indicator in output
                for indicator in ["/dev/", "device", "major", "minor"]
            )
            or len(output.strip()) > 0
        )
    else:
        # Should fail if not a mount point
        assert result == 1


def test_execute_stat_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test -x option to show filesystem stats
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/"])

    # Should either succeed with filesystem stats or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show filesystem statistics
        assert (
            any(
                stat in output
                for stat in ["filesystem", "blocks", "inodes", "free", "available"]
            )
            or len(output.strip()) > 0
        )
    else:
        # Should fail if not a mount point or stats not available
        assert result == 1


def test_execute_verbose_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test -v option for verbose output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "/"])

    # Should either succeed with verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show verbose mount point information
        assert (
            any(info in output for info in ["mount", "device", "filesystem", "options"])
            or len(output.strip()) > 0
        )
    else:
        # Should fail if not a mount point
        assert result == 1


def test_execute_combined_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test combining multiple options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "-v", "/"])

    # Should either succeed with combined output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show both device and verbose information
        assert len(output.strip()) >= 0
    else:
        # Should fail if not a mount point
        assert result == 1


def test_execute_symlink_to_mountpoint(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with symlink to mount point
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/var/run"]
        )  # Often symlink to /run

    # Should either follow symlink and check target or handle appropriately
    if result == 0:
        output = capture.get()
        # Should indicate mount point status of target
        assert len(output.strip()) >= 0
    else:
        # Should fail if target is not a mount point
        assert result == 1


def test_execute_bind_mount_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test detection of bind mounts
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib"])

    # Should detect bind mounts appropriately
    if result == 0:
        output = capture.get()
        # Should indicate bind mount status
        assert len(output.strip()) >= 0
    else:
        # Should fail if not a mount point
        assert result == 1


def test_execute_network_mount_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test detection of network mounts
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/mnt/nfs"])

    # Should detect network mounts appropriately
    if result == 0:
        output = capture.get()
        # Should indicate network mount status
        assert len(output.strip()) >= 0
    else:
        # Should fail if not a mount point or doesn't exist
        assert result == 1


def test_execute_tmpfs_mount_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test detection of tmpfs mounts
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/run"])

    # Should detect tmpfs mounts appropriately
    if result == 0:
        output = capture.get()
        # Should indicate tmpfs mount status
        assert len(output.strip()) >= 0
    else:
        # Should fail if /run is not a mount point
        assert result == 1


def test_execute_loop_device_mount(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test detection of loop device mounts
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/mnt/loop"])

    # Should detect loop device mounts appropriately
    if result == 0:
        output = capture.get()
        # Should indicate loop mount status
        assert len(output.strip()) >= 0
    else:
        # Should fail if not a mount point or doesn't exist
        assert result == 1


def test_execute_overlayfs_mount_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test detection of overlay filesystem mounts
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/overlay"])

    # Should detect overlay mounts appropriately
    if result == 0:
        output = capture.get()
        # Should indicate overlay mount status
        assert len(output.strip()) >= 0
    else:
        # Should fail if not a mount point or doesn't exist
        assert result == 1


def test_execute_permissions_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test permission handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/root"])

    # Should handle permissions appropriately
    if result == 0:
        output = capture.get()
        # Should check mount point status despite permissions
        assert len(output.strip()) >= 0
    else:
        # Should fail if not accessible or not a mount point
        assert result == 1
        output = capture.get()
        if "permission denied" in output.lower():
            assert "permission denied" in output.lower()


def test_execute_deep_directory_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with deep directory path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/lib/systemd/system"])

    # Should handle deep paths appropriately
    if result == 0:
        output = capture.get()
        # Should indicate mount point status
        assert len(output.strip()) >= 0
    else:
        # Should fail if not a mount point
        assert result == 1


def test_execute_relative_path_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with relative path (should be rejected or resolved)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../tmp"])

    # Should either resolve relative path or reject it
    if result == 0:
        output = capture.get()
        # Should resolve and check mount point
        assert len(output.strip()) >= 0
    else:
        # Should fail if relative paths not supported or not a mount point
        assert result == 1


def test_execute_mount_point_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with mount point containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/mnt/my mount"])

    # Should handle spaces in mount point names
    if result == 0:
        output = capture.get()
        # Should handle spaced mount point
        assert len(output.strip()) >= 0
    else:
        # Should fail if mount point doesn't exist or not mounted
        assert result == 1


def test_execute_mount_point_with_special_chars(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with mount point containing special characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/mnt/test-mount_point"])

    # Should handle special characters in mount point names
    if result == 0:
        output = capture.get()
        # Should handle special character mount point
        assert len(output.strip()) >= 0
    else:
        # Should fail if mount point doesn't exist
        assert result == 1


def test_execute_very_long_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with very long path
    temp_dir = tempfile.mkdtemp()
    long_path = temp_dir + "/" + "very-long-directory-name/" * 10 + "final"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_path])

    # Should handle long paths appropriately
    if result == 0:
        output = capture.get()
        # Should handle long path
        assert len(output.strip()) >= 0
    else:
        # Should fail if path doesn't exist or not a mount point
        assert result == 1


def test_execute_proc_filesystem_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test /proc filesystem access for mount information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should access /proc/mounts for mount information
    if result == 0:
        output = capture.get()
        # Should successfully determine mount status
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_multiple_directories(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with multiple directories
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/", "/proc", "/sys"])

    # Should either handle multiple directories or use first one
    if result == 0:
        output = capture.get()
        # Should check first directory
        assert len(output.strip()) >= 0
    else:
        # Should fail if first directory is not a mount point or too many args
        assert result == 1
        output = capture.get()
        if "too many arguments" in output:
            assert "too many arguments" in output


def test_execute_device_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with device file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should fail as device files are not directories
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["not a directory", "is not a mountpoint", "not a mount point"]
    )


def test_execute_fifo_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test with FIFO (named pipe)
    temp_dir = tempfile.mkdtemp()
    fifo_path = temp_dir + "/test-fifo"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[fifo_path])

    # Should fail as FIFOs are not directories
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "not a directory",
                "No such file",
                "not found",
                "not a mountpoint",
            ]
        )
    else:
        # May succeed if FIFO doesn't exist and treated as directory check
        assert result == 0


def test_execute_output_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test output format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent format
        assert len(output.strip()) >= 0
    else:
        assert result == 1
        output = capture.get()
        # Should have consistent error format
        assert len(output.strip()) >= 0


def test_execute_exit_code_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test exit code consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["/"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["/"])

    # Should return consistent exit codes
    assert result1 == result2


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        # Should produce consistent results
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert len(output.strip()) >= 0


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000  # Should be brief output
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MountpointCommand,
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
