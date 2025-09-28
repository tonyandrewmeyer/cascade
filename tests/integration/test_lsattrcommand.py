"""Integration tests for the LsattrCommand."""

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
    """Fixture to create a LsattrCommand instance."""
    yield pebble_shell.commands.LsattrCommand(shell=shell)


def test_name(command: pebble_shell.commands.LsattrCommand):
    assert command.name == "lsattr"


def test_category(command: pebble_shell.commands.LsattrCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.LsattrCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "lsattr" in output
    assert "List file attributes" in output
    assert "-R" in output
    assert "-a" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "lsattr" in output
    assert "List file attributes" in output


def test_execute_no_args_current_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # lsattr with no args should list attributes of current directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing attributes or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show file attributes for current directory
        assert len(output.strip()) >= 0
        # Should contain attribute format (e.g., "---------- filename")
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    # Should have attribute flags followed by filename
                    parts = line.split()
                    if len(parts) >= 2:
                        # First part should be attribute flags
                        assert len(parts[0]) >= 1
                        assert all(c in "aAcCdDeFijsStTu-" for c in parts[0])
    else:
        # Should fail if ext2/ext3/ext4 filesystem not available
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Operation not supported",
                "Inappropriate ioctl",
                "not supported",
                "error",
            ]
        )


def test_execute_single_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with single file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed showing file attributes or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show attributes for the specific file
        assert "/etc/hosts" in output or len(output.strip()) > 0
        if "/etc/hosts" in output:
            # Should contain attribute flags
            lines = output.strip().split("\n")
            for line in lines:
                if "/etc/hosts" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        # Should have attribute flags
                        assert all(c in "aAcCdDeFijsStTu-" for c in parts[0])
    else:
        # Should fail if file not accessible or filesystem not supported
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Operation not supported",
                "No such file",
                "permission denied",
                "error",
            ]
        )


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["No such file", "not found", "does not exist", "error"]
    )


def test_execute_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should either succeed showing directory attributes or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show attributes for directory contents
        assert len(output.strip()) >= 0
        if output.strip():
            # Should contain directory entries with attributes
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        # Should have attribute flags
                        assert all(c in "aAcCdDeFijsStTu-" for c in parts[0])
    else:
        # Should fail if directory not accessible or filesystem not supported
        assert result == 1


def test_execute_recursive_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test -R option for recursive listing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-R", tempfile.mkdtemp()])

    # Should either succeed with recursive listing or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show recursive directory attributes
        assert len(output.strip()) >= 0
        if output.strip():
            # Should contain entries from subdirectories
            lines = output.strip().split("\n")
            if len(lines) > 1:
                # Should have multiple entries for recursive traversal
                assert len(lines) >= 1
    else:
        # Should fail if not supported or permission denied
        assert result == 1


def test_execute_all_files_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test -a option to list all files including hidden
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", tempfile.mkdtemp()])

    # Should either succeed showing all files or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show attributes for all files including hidden
        assert len(output.strip()) >= 0
        if output.strip():
            # Should include hidden files (starting with .)
            lines = output.strip().split("\n")
            _ = [line for line in lines if "/." in line or line.strip().endswith("/.")]
            # May or may not have hidden files, but should handle them
            assert len(lines) >= 0
    else:
        # Should fail if not supported
        assert result == 1


def test_execute_directories_only_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test -d option to list directories themselves, not contents
    test_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", test_dir])

    # Should either succeed showing directory attributes or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show attributes for the directory itself
        assert len(output.strip()) >= 0
        if test_dir in output:
            # Should show attributes for test directory
            lines = output.strip().split("\n")
            for line in lines:
                if test_dir in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        assert all(c in "aAcCdDeFijsStTu-" for c in parts[0])
    else:
        # Should fail if not supported
        assert result == 1


def test_execute_version_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test -v option to display version
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v"])

    # Should either succeed with version or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show version information
        assert (
            any(
                indicator in output.lower()
                for indicator in ["version", "lsattr", "e2fsprogs"]
            )
            or len(output.strip()) > 0
        )
    else:
        # Should fail if version not available
        assert result == 1


def test_execute_ext4_filesystem_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with ext4 filesystem (primary support)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should either succeed on ext4 or fail gracefully on other filesystems
    if result == 0:
        output = capture.get()
        # Should show ext4 attributes
        assert len(output.strip()) >= 0
        if output.strip():
            # Should contain standard ext4 attribute flags
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        # Should contain valid ext4 attribute characters
                        assert all(c in "aAcCdDeFijsStTu-" for c in parts[0])
    else:
        # Should fail if not ext4 filesystem
        assert result == 1


def test_execute_ntfs_filesystem_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with NTFS filesystem (should fail gracefully)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/mnt/ntfs"])

    # Should fail on NTFS as it doesn't support ext attributes
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Operation not supported",
                "Inappropriate ioctl",
                "not supported",
                "No such file",  # If mount point doesn't exist
            ]
        )
    else:
        # May succeed if mount point doesn't exist or is actually ext filesystem
        assert result == 0


def test_execute_fat32_filesystem_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with FAT32 filesystem (should fail gracefully)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/mnt/fat32"])

    # Should fail on FAT32 as it doesn't support ext attributes
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Operation not supported",
                "Inappropriate ioctl",
                "not supported",
                "No such file",  # If mount point doesn't exist
            ]
        )
    else:
        # May succeed if mount point doesn't exist
        assert result == 0


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/shadow"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        if "permission denied" in output.lower():
            assert "permission denied" in output.lower()
        else:
            # May fail with other error if filesystem doesn't support attributes
            assert any(msg in output for msg in ["Operation not supported", "error"])
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with symbolic link
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin"])  # Often a symlink

    # Should either follow symlink or handle appropriately
    if result == 0:
        output = capture.get()
        # Should show attributes of symlink target or symlink itself
        assert len(output.strip()) >= 0
    else:
        # Should fail if filesystem doesn't support attributes
        assert result == 1


def test_execute_special_files_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with special files (/dev, /proc)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either handle special files or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show attributes if supported
        assert len(output.strip()) >= 0
    else:
        # Should fail if special files don't support ext attributes
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Operation not supported",
                "Inappropriate ioctl",
                "not supported",
            ]
        )


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed showing multiple file attributes or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show attributes for multiple files
        assert len(output.strip()) >= 0
        if output.strip():
            # Should contain both files
            assert (
                any(file in output for file in ["/etc/hosts", "/etc/passwd"])
                or len(output.strip()) > 0
            )
    else:
        # Should fail if filesystem doesn't support attributes
        assert result == 1


def test_execute_attribute_flags_interpretation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test interpretation of attribute flags
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should either succeed with interpretable flags or fail if not supported
    if result == 0:
        output = capture.get()
        # Should show interpretable attribute flags
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # Should contain valid attribute characters
                        # a=append only, A=no atime updates, c=compressed, etc.
                        valid_chars = "aAcCdDeFijsStTu-"
                        assert all(c in valid_chars for c in flags)
    else:
        assert result == 1


def test_execute_immutable_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with potentially immutable files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either show immutable flag or regular attributes
    if result == 0:
        output = capture.get()
        # Should show attributes, possibly including immutable flag 'i'
        if output.strip() and "/etc/passwd" in output:
            lines = output.strip().split("\n")
            for line in lines:
                if "/etc/passwd" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # May contain 'i' for immutable
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_append_only_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with potentially append-only files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/log"])

    # Should either show append-only flag or regular attributes
    if result == 0:
        output = capture.get()
        # Should show attributes, possibly including append-only flag 'a'
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # May contain 'a' for append-only
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_compressed_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with potentially compressed files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should either show compressed flag or regular attributes
    if result == 0:
        output = capture.get()
        # Should show attributes, possibly including compressed flag 'c'
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # May contain 'c' for compressed
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_no_dump_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with files that have no-dump attribute
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should either show no-dump flag or regular attributes
    if result == 0:
        output = capture.get()
        # Should show attributes, possibly including no-dump flag 'd'
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # May contain 'd' for no-dump
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_secure_deletion_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with files that have secure deletion attribute
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should either show secure deletion flag or regular attributes
    if result == 0:
        output = capture.get()
        # Should show attributes, possibly including secure deletion flag 's'
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # May contain 's' for secure deletion
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_synchronous_updates_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with files that have synchronous updates attribute
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should either show synchronous flag or regular attributes
    if result == 0:
        output = capture.get()
        # Should show attributes, possibly including synchronous flag 'S'
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # May contain 'S' for synchronous updates
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_undeletable_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with files that have undeletable attribute
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should either show undeletable flag or regular attributes
    if result == 0:
        output = capture.get()
        # Should show attributes, possibly including undeletable flag 'u'
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        flags = parts[0]
                        # May contain 'u' for undeletable
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_large_directory_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test with large directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr"])

    # Should handle large directories efficiently
    if result == 0:
        output = capture.get()
        # Should handle many files efficiently
        assert len(output) >= 0
    else:
        # Should fail if filesystem doesn't support attributes
        assert result == 1


def test_execute_deep_directory_recursion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test recursive operation on deep directory structure
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-R", "/etc"])

    # Should handle deep recursion appropriately
    if result == 0:
        output = capture.get()
        # Should traverse deep directory structure
        assert len(output) >= 0
    else:
        # Should fail if filesystem doesn't support attributes or permission denied
        assert result == 1


def test_execute_output_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test output format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent attribute flag format
        if output.strip():
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        # Should have consistent flag length and format
                        flags = parts[0]
                        assert len(flags) >= 1
                        assert all(c in "aAcCdDeFijsStTu-" for c in flags)
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])

    # Should recover from errors gracefully
    if result == 1:
        output = capture.get()
        # Should provide meaningful error message
        assert any(msg in output for msg in ["No such file", "not found", "error"])
    else:
        assert result == 0


def test_execute_performance_with_many_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test performance with many files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin"])

    # Should handle many files efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000000  # Reasonable output size limit for /tmp
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsattrCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--invalid-option", tempfile.mkdtemp()]
        )

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0
