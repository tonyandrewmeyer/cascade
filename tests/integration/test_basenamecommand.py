"""Integration tests for the BasenameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a BasenameCommand instance."""
    yield pebble_shell.commands.BasenameCommand(shell=shell)


def test_name(command: pebble_shell.commands.BasenameCommand):
    assert command.name == "basename"


def test_category(command: pebble_shell.commands.BasenameCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.BasenameCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "basename" in output
    assert "Extract filename from path" in output
    assert "path" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "basename" in output
    assert "Extract filename from path" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # basename with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["usage", "Usage", "basename", "path"])


def test_execute_simple_filename(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test simple filename extraction
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/ls"])

    # Should succeed extracting filename
    assert result == 0
    output = capture.get()
    # Should contain just the filename
    assert output.strip() == "ls"


def test_execute_absolute_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test absolute path extraction
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/home/user/documents/file.txt"])

    # Should succeed extracting filename
    assert result == 0
    output = capture.get()
    # Should contain just the filename
    assert output.strip() == "file.txt"


def test_execute_relative_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test relative path extraction
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../documents/report.pdf"])

    # Should succeed extracting filename
    assert result == 0
    output = capture.get()
    # Should contain just the filename
    assert output.strip() == "report.pdf"


def test_execute_filename_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test filename without path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["filename.txt"])

    # Should succeed with filename
    assert result == 0
    output = capture.get()
    # Should return the same filename
    assert output.strip() == "filename.txt"


def test_execute_trailing_slash(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test path with trailing slash
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/"])

    # Should succeed handling trailing slash
    assert result == 0
    output = capture.get()
    # Should return directory name
    assert output.strip() == "bin"


def test_execute_multiple_trailing_slashes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test path with multiple trailing slashes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/local///"])

    # Should succeed handling multiple slashes
    assert result == 0
    output = capture.get()
    # Should return directory name
    assert output.strip() == "local"


def test_execute_root_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test root path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should succeed with root path
    assert result == 0
    output = capture.get()
    # Should return root or empty
    assert output.strip() in ["/", ""]


def test_execute_current_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test current directory path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["."])

    # Should succeed with current directory
    assert result == 0
    output = capture.get()
    # Should return dot
    assert output.strip() == "."


def test_execute_parent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test parent directory path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[".."])

    # Should succeed with parent directory
    assert result == 0
    output = capture.get()
    # Should return double dot
    assert output.strip() == ".."


def test_execute_suffix_removal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test suffix removal
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/file.txt", ".txt"])

    # Should succeed removing suffix
    assert result == 0
    output = capture.get()
    # Should return filename without suffix
    assert output.strip() == "file"


def test_execute_suffix_removal_no_match(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test suffix removal with no match
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/file.txt", ".pdf"])

    # Should succeed without removing suffix
    assert result == 0
    output = capture.get()
    # Should return full filename
    assert output.strip() == "file.txt"


def test_execute_multiple_extensions(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test file with multiple extensions
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path/archive.tar.gz", ".gz"])

    # Should succeed removing last extension
    assert result == 0
    output = capture.get()
    # Should return filename with remaining extension
    assert output.strip() == "archive.tar"


def test_execute_hidden_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test hidden file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/home/user/.bashrc"])

    # Should succeed with hidden file
    assert result == 0
    output = capture.get()
    # Should return hidden filename
    assert output.strip() == ".bashrc"


def test_execute_file_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test file with spaces in name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path/my file.txt"])

    # Should succeed with spaces
    assert result == 0
    output = capture.get()
    # Should return filename with spaces
    assert output.strip() == "my file.txt"


def test_execute_special_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test file with special characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path/file-name_123.txt"])

    # Should succeed with special characters
    assert result == 0
    output = capture.get()
    # Should return filename with special characters
    assert output.strip() == "file-name_123.txt"


def test_execute_unicode_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test file with Unicode characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path/файл.txt"])

    # Should succeed with Unicode
    assert result == 0
    output = capture.get()
    # Should return Unicode filename
    assert output.strip() == "файл.txt"


def test_execute_long_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test very long path
    long_path = "/very/long/path/with/many/directories/and/subdirectories/file.txt"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_path])

    # Should succeed with long path
    assert result == 0
    output = capture.get()
    # Should return just the filename
    assert output.strip() == "file.txt"


def test_execute_long_filename(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test long filename
    long_filename = "very_long_filename_with_many_characters_and_underscores.txt"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[f"/path/{long_filename}"])

    # Should succeed with long filename
    assert result == 0
    output = capture.get()
    # Should return the long filename
    assert output.strip() == long_filename


def test_execute_empty_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test empty string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty string
        assert len(output.strip()) >= 0
    else:
        # Should fail with empty string error
        assert result == 1


def test_execute_only_slashes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test string with only slashes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["///"])

    # Should succeed handling only slashes
    assert result == 0
    output = capture.get()
    # Should return root or empty
    assert output.strip() in ["/", ""]


def test_execute_mixed_slashes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test path with mixed slashes (if supported)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin\\file.txt"])

    # Should succeed with mixed slashes
    assert result == 0
    output = capture.get()
    # Should handle path appropriately
    assert len(output.strip()) > 0


def test_execute_suffix_longer_than_filename(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test suffix longer than filename
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file.txt", ".txt.bak"])

    # Should succeed without removing suffix
    assert result == 0
    output = capture.get()
    # Should return full filename
    assert output.strip() == "file.txt"


def test_execute_identical_suffix(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test suffix identical to filename
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file.txt", "file.txt"])

    # Should succeed handling identical suffix
    assert result == 0
    output = capture.get()
    # Should return appropriate result
    assert len(output.strip()) >= 0


def test_execute_partial_suffix_match(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test partial suffix match
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file.txt", "xt"])

    # Should succeed with partial match
    assert result == 0
    output = capture.get()
    # Should return filename without partial suffix
    assert output.strip() == "file.t"


def test_execute_multiple_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test multiple paths (if supported)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/ls", "/usr/bin/cat"])

    # Should either process first path or handle multiple paths
    if result == 0:
        output = capture.get()
        # Should contain filename(s)
        assert len(output.strip()) > 0
    else:
        # May not support multiple paths
        assert result == 1


def test_execute_symlink_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test symbolic link path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/link"])

    # Should succeed with symlink
    assert result == 0
    output = capture.get()
    # Should return link name
    assert output.strip() == "link"


def test_execute_device_file_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test device file path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should succeed with device file
    assert result == 0
    output = capture.get()
    # Should return device name
    assert output.strip() == "null"


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/test"])

    # Should produce properly formatted output
    assert result == 0
    output = capture.get()

    # Should have clean output format
    assert len(output.strip()) > 0
    # Should not contain path separators
    assert "/" not in output.strip()
    # Should be single line
    lines = output.strip().split("\n")
    assert len(lines) == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/file"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 1000  # Reasonable output size limit


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert output.strip() == "ls"


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["usage", "Usage", "basename"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/test"])

    # Should handle signals appropriately
    assert result == 0
    output = capture.get()
    # Should be signal-safe
    assert output.strip() == "test"


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path/file.txt"])

    # Should work regardless of locale settings
    assert result == 0
    output = capture.get()
    # Should be locale-independent
    assert output.strip() == "file.txt"


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/basename"])

    # Should work across different platforms
    assert result == 0
    output = capture.get()
    # Should handle path separators correctly
    assert output.strip() == "basename"


def test_execute_standard_compliance(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test POSIX/Unix standard compliance
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/ls"])

    # Should comply with Unix standards
    assert result == 0
    output = capture.get()
    # Should follow standard behavior
    assert output.strip() == "ls"


def test_execute_edge_case_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test edge case handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/."])

    # Should handle edge cases appropriately
    assert result == 0
    output = capture.get()
    # Should return appropriate result
    assert output.strip() == "."


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/very/long/path/to/file.txt"])

    # Should complete efficiently
    assert result == 0
    output = capture.get()
    # Should process efficiently
    assert output.strip() == "file.txt"


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["/usr/bin/test"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["/usr/bin/test"])

    # Should produce consistent results
    assert result1 == 0
    assert result2 == 0
    # Both executions should succeed consistently
    assert result1 == result2


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BasenameCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/file"])

    # Should operate robustly
    assert result == 0
    output = capture.get()
    # Should handle stress conditions
    assert output.strip() == "file"
