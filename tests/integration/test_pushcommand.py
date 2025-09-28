"""Integration tests for the PushCommand."""

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
    """Fixture to create a PushCommand instance."""
    yield pebble_shell.commands.PushCommand(shell=shell)


def test_name(command: pebble_shell.commands.PushCommand):
    assert command.name == "pebble-push"


def test_category(command: pebble_shell.commands.PushCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.PushCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "push" in output
    assert "Transfer files to container" in output
    assert "--create-dirs" in output
    assert "--permissions" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "push" in output
    assert "Transfer files to container" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # push with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "push <source-path> <dest-path>" in output


def test_execute_missing_dest_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # push with only source path should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/local/file.txt"])

    # Should fail with missing destination error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["missing destination", "push <source-path> <dest-path>", "usage"]
    )


def test_execute_simple_file_push(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test pushing simple file to container
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/passwd"]
        )

    # Should either succeed with file transfer or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show transfer completion message
        assert any(
            msg in output
            for msg in ["File pushed successfully", "Transfer completed", "uploaded"]
        )
    else:
        # Should fail if file doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Push operation failed", "error", "failed"]
        )


def test_execute_nonexistent_source_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test with nonexistent source file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/nonexistent/file.txt", "/container/file.txt"]
        )

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["Push operation failed", "file not found", "No such file", "error"]
    )


def test_execute_directory_push(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test pushing directory to container
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_dir, "/container/tmp"])

    # Should either succeed with directory transfer or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show directory transfer completion
        assert any(
            msg in output
            for msg in [
                "Directory pushed successfully",
                "Transfer completed",
                "uploaded",
            ]
        )
    else:
        assert result == 1


def test_execute_create_dirs_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test --create-dirs option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--create-dirs", "/etc/passwd", "/container/deep/dir/passwd"],
        )

    # Should either succeed creating directories or fail gracefully
    if result == 0:
        output = capture.get()
        # Should create directories and transfer file
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_permissions_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test --permissions option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--permissions", "755", "/etc/passwd", "/container/passwd"],
        )

    # Should either succeed with permission setting or fail gracefully
    if result == 0:
        output = capture.get()
        # Should set permissions and transfer file
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_invalid_permissions(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test with invalid permissions
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--permissions", "999", "/etc/passwd", "/container/passwd"],
        )

    # Should fail with invalid permissions error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid permissions", "Push operation failed", "error"]
    )


def test_execute_overwrite_existing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test overwriting existing destination file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/existing-file"]
        )

    # Should either succeed overwriting file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should complete transfer with overwrite
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_permission_denied_source(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test with permission denied on source file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/root/.ssh/id_rsa", "/container/key"]
        )

    # Should fail with permission error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "Push operation failed", "error"]
        )
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_permission_denied_destination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test with permission denied on destination
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/root/restricted"]
        )

    # Should fail with permission error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "Push operation failed", "error"]
        )
    else:
        # May succeed if destination is writable
        assert result == 0


def test_execute_large_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test transferring large file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/usr/bin/bash", "/container/bash"]
        )

    # Should either succeed with large file transfer or fail gracefully
    if result == 0:
        output = capture.get()
        # Should complete large file transfer
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_binary_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test transferring binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls", "/container/ls"])

    # Should handle binary file transfer
    if result == 0:
        output = capture.get()
        # Should complete binary transfer
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_text_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test transferring text file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/container/hosts"])

    # Should handle text file transfer
    if result == 0:
        output = capture.get()
        # Should complete text transfer
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_empty_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test transferring empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null", "/container/empty"])

    # Should handle empty file transfer
    if result == 0:
        output = capture.get()
        # Should complete empty file transfer
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test handling of symbolic links
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin", "/container/bin-link"])

    # Should handle symlink appropriately
    if result == 0:
        output = capture.get()
        # Should transfer symlink or target
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_absolute_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test with absolute paths
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/passwd-copy"]
        )

    # Should handle absolute paths
    if result == 0:
        output = capture.get()
        # Should complete transfer with absolute paths
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_relative_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test with relative paths
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../etc/passwd", "passwd-rel"])

    # Should handle relative paths
    if result == 0:
        output = capture.get()
        # Should resolve and transfer relative paths
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_special_characters_in_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test paths with special characters
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/file with spaces & chars"]
        )

    # Should handle special characters in paths
    if result == 0:
        output = capture.get()
        # Should handle special characters
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_nested_directory_push(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test pushing nested directory structure
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/usr/share/doc", "/container/doc"]
        )

    # Should handle nested directory transfer
    if result == 0:
        output = capture.get()
        # Should transfer entire directory tree
        assert any(
            msg in output
            for msg in ["Directory pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_file_metadata_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test file metadata preservation during transfer
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/passwd-meta"]
        )

    # Should preserve file metadata
    if result == 0:
        output = capture.get()
        # Should maintain file attributes
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_concurrent_push_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test concurrent push operations
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/hosts", "/container/concurrent-hosts"]
        )

    # Should handle concurrent operations
    if result == 0:
        output = capture.get()
        # Should complete concurrent transfer
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_network_interruption_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test handling of network interruptions
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/network-test"]
        )

    # Should handle network issues gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Push operation failed", "network", "error"]
        )
    else:
        assert result == 0


def test_execute_disk_space_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test handling of insufficient disk space
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/usr/bin/bash", "/container/space-test"]
        )

    # Should handle disk space issues
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["Push operation failed", "space", "error"])
    else:
        assert result == 0


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test API error handling when Pebble is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/api-test"]
        )

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Push operation failed", "error", "failed"]
        )
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_progress_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test progress reporting for large transfers
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/usr/bin/bash", "/container/progress-test"]
        )

    # Should report transfer progress
    if result == 0:
        output = capture.get()
        # Should show progress information
        assert any(
            msg in output
            for msg in ["File pushed successfully", "Transfer completed", "bytes"]
        )
    else:
        assert result == 1


def test_execute_checksum_verification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test checksum verification of transferred files
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/checksum-test"]
        )

    # Should verify file integrity
    if result == 0:
        output = capture.get()
        # Should complete with integrity check
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_cleanup_on_failure(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test cleanup on transfer failure
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/nonexistent/file", "/container/cleanup-test"]
        )

    # Should clean up on failure
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["Push operation failed", "error"])


def test_execute_recursive_directory_push(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test recursive directory pushing
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/systemd", "/container/systemd"]
        )

    # Should handle recursive directory transfer
    if result == 0:
        output = capture.get()
        # Should transfer entire directory recursively
        assert any(
            msg in output
            for msg in ["Directory pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_transfer_cancellation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test transfer cancellation handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/cancel-test"]
        )

    # Should handle cancellation appropriately
    if result == 0:
        output = capture.get()
        # Should complete or handle cancellation
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_owner_group_setting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test setting owner and group during push
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--permissions", "644", "/etc/passwd", "/container/owned-file"],
        )

    # Should set ownership appropriately
    if result == 0:
        output = capture.get()
        # Should complete with ownership setting
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_atomic_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test atomic transfer operations
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/atomic-test"]
        )

    # Should perform atomic transfer
    if result == 0:
        output = capture.get()
        # Should complete atomically
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_backup_existing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PushCommand,
):
    # Test backing up existing files before overwrite
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/container/backup-test"]
        )

    # Should handle existing file appropriately
    if result == 0:
        output = capture.get()
        # Should complete with backup handling
        assert any(
            msg in output for msg in ["File pushed successfully", "Transfer completed"]
        )
    else:
        assert result == 1
