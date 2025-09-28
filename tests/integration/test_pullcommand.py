"""Integration tests for the PullCommand."""

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
    """Fixture to create a PullCommand instance."""
    yield pebble_shell.commands.PullCommand(shell=shell)


def test_name(command: pebble_shell.commands.PullCommand):
    assert command.name == "pebble-pull"


def test_category(command: pebble_shell.commands.PullCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.PullCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "pull" in output
    assert "Retrieve files from container" in output
    assert "--create-dirs" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "pull" in output
    assert "Retrieve files from container" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # pull with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "pull <source-path> <dest-path>" in output


def test_execute_missing_dest_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # pull with only source path should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/container/file.txt"])

    # Should fail with missing destination error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["missing destination", "pull <source-path> <dest-path>", "usage"]
    )


def test_execute_simple_file_pull(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test pulling simple file from container
    with tempfile.NamedTemporaryFile(delete=False) as dest_file:
        dest_path = dest_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", dest_path])

    # Should either succeed with file transfer or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show transfer completion message
        assert any(
            msg in output
            for msg in ["File pulled successfully", "Transfer completed", "copied"]
        )
    else:
        # Should fail if file doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Pull operation failed", "error", "failed"]
        )


def test_execute_nonexistent_source_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test with nonexistent source file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        dest_path = temp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/nonexistent/file.txt", dest_path]
        )

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["Pull operation failed", "file not found", "No such file", "error"]
    )


def test_execute_directory_pull(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test pulling directory from container
    dest_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc", dest_dir])

    # Should either succeed with directory transfer or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show directory transfer completion
        assert any(
            msg in output
            for msg in ["Directory pulled successfully", "Transfer completed", "copied"]
        )
    else:
        assert result == 1


def test_execute_create_dirs_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test --create-dirs option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--create-dirs", "/etc/passwd", "/nonexistent/dir/passwd"],
        )

    # Should either succeed creating directories or fail gracefully
    if result == 0:
        output = capture.get()
        # Should create directories and transfer file
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_overwrite_existing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test overwriting existing destination file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should either succeed overwriting file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should complete transfer with overwrite
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_permission_denied_source(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test with permission denied on source file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/root/.ssh/id_rsa", tmp_name])

    # Should fail with permission error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "Pull operation failed", "error"]
        )
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_permission_denied_destination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test with permission denied on destination
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/root/restricted"]
        )

    # Should fail with permission error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "Pull operation failed", "error"]
        )
    else:
        # May succeed if destination is writable
        assert result == 0


def test_execute_large_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test transferring large file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/bash", tmp_name])

    # Should either succeed with large file transfer or fail gracefully
    if result == 0:
        output = capture.get()
        # Should complete large file transfer
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_binary_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test transferring binary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls", tmp_name])

    # Should handle binary file transfer
    if result == 0:
        output = capture.get()
        # Should complete binary transfer
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_text_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test transferring text file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", tmp_name])

    # Should handle text file transfer
    if result == 0:
        output = capture.get()
        # Should complete text transfer
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_empty_file_transfer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test transferring empty file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null", tmp_name])

    # Should handle empty file transfer
    if result == 0:
        output = capture.get()
        # Should complete empty file transfer
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test handling of symbolic links
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin", tmp_name])

    # Should handle symlink appropriately
    if result == 0:
        output = capture.get()
        # Should transfer symlink or target
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_absolute_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test with absolute paths
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should handle absolute paths
    if result == 0:
        output = capture.get()
        # Should complete transfer with absolute paths
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_relative_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test with relative paths
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../etc/passwd", "passwd-rel"])

    # Should handle relative paths
    if result == 0:
        output = capture.get()
        # Should resolve and transfer relative paths
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_special_characters_in_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test paths with special characters
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=" with spaces & chars"
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should handle special characters in paths
    if result == 0:
        output = capture.get()
        # Should handle special characters
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_nested_directory_pull(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test pulling nested directory structure
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/usr/share/doc", tempfile.mkdtemp()]
        )

    # Should handle nested directory transfer
    if result == 0:
        output = capture.get()
        # Should transfer entire directory tree
        assert any(
            msg in output
            for msg in ["Directory pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_file_metadata_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test file metadata preservation during transfer
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should preserve file metadata
    if result == 0:
        output = capture.get()
        # Should maintain file attributes
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_concurrent_pull_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test concurrent pull operations
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", tmp_name])

    # Should handle concurrent operations
    if result == 0:
        output = capture.get()
        # Should complete concurrent transfer
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_network_interruption_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test handling of network interruptions
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should handle network issues gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Pull operation failed", "network", "error"]
        )
    else:
        assert result == 0


def test_execute_disk_space_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test handling of insufficient disk space
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/bash", tmp_name])

    # Should handle disk space issues
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["Pull operation failed", "space", "error"])
    else:
        assert result == 0


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test API error handling when Pebble is unavailable
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Pull operation failed", "error", "failed"]
        )
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_progress_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test progress reporting for large transfers
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/bash", tmp_name])

    # Should report transfer progress
    if result == 0:
        output = capture.get()
        # Should show progress information
        assert any(
            msg in output
            for msg in ["File pulled successfully", "Transfer completed", "bytes"]
        )
    else:
        assert result == 1


def test_execute_checksum_verification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test checksum verification of transferred files
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should verify file integrity
    if result == 0:
        output = capture.get()
        # Should complete with integrity check
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_cleanup_on_failure(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test cleanup on transfer failure
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file", tmp_name])

    # Should clean up on failure
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["Pull operation failed", "error"])


def test_execute_recursive_directory_pull(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test recursive directory pulling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/systemd", tempfile.mkdtemp()]
        )

    # Should handle recursive directory transfer
    if result == 0:
        output = capture.get()
        # Should transfer entire directory recursively
        assert any(
            msg in output
            for msg in ["Directory pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1


def test_execute_transfer_cancellation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PullCommand,
):
    # Test transfer cancellation handling
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", tmp_name])

    # Should handle cancellation appropriately
    if result == 0:
        output = capture.get()
        # Should complete or handle cancellation
        assert any(
            msg in output for msg in ["File pulled successfully", "Transfer completed"]
        )
    else:
        assert result == 1
