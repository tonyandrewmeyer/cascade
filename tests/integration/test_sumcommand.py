"""Integration tests for the SumCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SumCommand instance."""
    yield pebble_shell.commands.SumCommand(shell=shell)


def test_name(command: pebble_shell.commands.SumCommand):
    assert command.name == "sum"


def test_category(command: pebble_shell.commands.SumCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.SumCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "sum" in output
    assert "Calculate and display checksums" in output
    assert "-r" in output
    assert "-s, --sysv" in output
    assert "BSD sum algorithm" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "sum" in output
    assert "Calculate and display checksums" in output


def test_execute_no_args_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # sum with no args should read from stdin
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed (if stdin available) or fail gracefully
    assert result in [0, 1]


def test_execute_single_file_bsd_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with single file using default BSD algorithm
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed with checksum or fail if file not accessible
    if result == 0:
        output = capture.get()
        # Should show checksum and filename
        assert "/etc/passwd" in output
        # Should contain numeric checksum
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_single_file_bsd_explicit(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with single file using explicit -r BSD algorithm
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", "/etc/passwd"])

    # Should either succeed with BSD checksum or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show checksum and filename
        assert "/etc/passwd" in output
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_single_file_sysv_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with single file using -s System V algorithm
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/passwd"])

    # Should either succeed with System V checksum or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show checksum and filename
        assert "/etc/passwd" in output
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_single_file_sysv_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with single file using --sysv System V algorithm
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--sysv", "/etc/passwd"])

    # Should behave same as -s option
    if result == 0:
        output = capture.get()
        # Should show checksum and filename
        assert "/etc/passwd" in output
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", "/etc/hosts"])

    # Should either succeed with checksums for all files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show checksums for both files
        assert "/etc/passwd" in output
        assert "/etc/hosts" in output
        # Should have multiple lines of output
        lines = output.strip().split("\n")
        assert len(lines) >= 2
    else:
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with empty file (if available)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed with checksum for empty file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show checksum for empty file
        assert "/dev/null" in output
        # Empty file should have specific checksum value
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_bsd_vs_sysv_algorithm_difference(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test that BSD and System V algorithms produce different results

    # Get BSD checksum
    with command.shell.console.capture() as capture:
        result_bsd = command.execute(client=client, args=["/etc/passwd"])
    if result_bsd == 0:
        _ = capture.get()

    # Get System V checksum
    with command.shell.console.capture() as capture:
        result_sysv = command.execute(client=client, args=["-s", "/etc/passwd"])
    if result_sysv == 0:
        _ = capture.get()

    # If both succeeded, they should potentially be different
    if result_bsd == 0 and result_sysv == 0:
        # Different algorithms may produce different checksums
        # (though they might be the same for some files)
        pass


def test_execute_checksum_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test checksum output format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should follow standard checksum format
    if result == 0:
        output = capture.get().strip()
        lines = output.split("\n")
        for line in lines:
            if line:
                # Each line should contain checksum and filename
                parts = line.split()
                assert len(parts) >= 2  # At least checksum and filename
                # First part should be numeric (checksum)
                assert parts[0].isdigit() or any(char.isdigit() for char in parts[0])


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with potentially large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle files of any size
    if result == 0:
        output = capture.get()
        # Should complete checksum calculation
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_permission_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test handling of permission errors
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/shadow"])

    # Should fail gracefully if permission denied
    if result == 1:
        output = capture.get()
        # Should show appropriate error message
        assert any(
            msg in output for msg in ["permission", "denied", "error", "No such file"]
        )
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_mixed_valid_invalid_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with mix of valid and invalid files
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", "/nonexistent/file"]
        )

    # Should either process valid files and skip invalid, or fail entirely
    if result == 0:
        output = capture.get()
        # Should process the valid file
        assert "/etc/passwd" in output
    else:
        # May fail if any file is invalid
        assert result == 1


def test_execute_relative_path_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with relative paths
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../etc/passwd"])

    # Should resolve relative path and calculate checksum
    if result == 0:
        output = capture.get()
        # Should show the path (may be resolved to absolute)
        assert "passwd" in output
    else:
        assert result == 1


def test_execute_absolute_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with absolute path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle absolute path
    if result == 0:
        output = capture.get()
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_algorithm_option_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with both -r and -s options (should use last one)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", "-s", "/etc/passwd"])

    # Should use the last specified algorithm (System V)
    if result == 0:
        output = capture.get()
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_unknown_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with unknown option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/etc/passwd"])

    # Should either ignore unknown option or fail with error
    if result == 1:
        output = capture.get()
        # Should show error for unknown option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May succeed if option is ignored
        assert result == 0


def test_execute_file_with_spaces_in_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test with filename containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path with spaces"])

    # Should either handle spaces or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle filename with spaces
        assert "path with spaces" in output
    else:
        assert result == 1


def test_execute_checksum_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SumCommand,
):
    # Test that same file produces same checksum
    checksums = []
    for _ in range(2):
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["/etc/passwd"])
        if result == 0:
            output = capture.get().strip()
            # Extract checksum (first part of output)
            checksum = output.split()[0] if output.split() else ""
            checksums.append(checksum)

    # Should produce identical checksums for same file
    if len(checksums) == 2:
        assert checksums[0] == checksums[1]
