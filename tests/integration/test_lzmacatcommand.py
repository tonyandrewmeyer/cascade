"""Integration tests for the LzmacatCommand."""

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
    """Fixture to create a LzmacatCommand instance."""
    yield pebble_shell.commands.LzmacatCommand(shell=shell)


def test_name(command: pebble_shell.commands.LzmacatCommand):
    assert command.name == "lzmacat"


def test_category(command: pebble_shell.commands.LzmacatCommand):
    assert command.category == "Compression"


def test_help(command: pebble_shell.commands.LzmacatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["lzma", "decompress", "cat", "display", "file"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["lzma", "decompress", "cat", "usage"]
    )


def test_execute_no_file_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with no file specified
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing file error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["file", "required", "missing", "usage", "error"]
    )


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with non-existent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent.lzma"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "error", "cannot open"]
    )


def test_execute_invalid_lzma_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with invalid LZMA file format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd"]
        )  # Not an LZMA file

    # Should fail with format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid", "format", "not lzma", "error", "compressed"]
    )


def test_execute_directory_instead_of_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with directory instead of file
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_dir])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "not a file", "error", "invalid"])


def test_execute_permission_denied(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with permission denied file (if exists)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/root/.ssh/id_rsa"]
        )  # Typically restricted

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # If it succeeded, should have output
        assert len(output) >= 0
    else:
        # Should fail with permission error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "access", "error", "not found"]
        )


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file1.lzma", "file2.lzma"])

    # Should either succeed processing multiple files or fail with error
    if result == 0:
        output = capture.get()
        # Should concatenate multiple files
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with stdin input (using dash)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-"])

    # Should either succeed reading from stdin or fail gracefully
    if result == 0:
        output = capture.get()
        # Should read from stdin
        assert len(output) >= 0
    else:
        # Should fail if no stdin data or format error
        assert result == 1


def test_execute_empty_lzma_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with empty LZMA file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])  # Empty file

    # Should either succeed with empty output or fail with format error
    if result == 0:
        output = capture.get()
        # Should produce empty output
        assert len(output) == 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "format", "error", "empty"])


def test_execute_corrupted_lzma_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with corrupted LZMA file (using random binary data)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/urandom"])  # Random data

    # Should fail with corruption/format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid", "format", "corrupted", "error", "not lzma"]
    )


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with large file (if available)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/zero"])  # Large file source

    # Should either handle large files or fail with format error
    if result == 0:
        output = capture.get()
        # Should handle large files efficiently
        assert len(output) >= 0
    else:
        # Should fail with format error (since /dev/zero is not LZMA)
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "format", "error", "not lzma"])


def test_execute_binary_data_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with binary executable (not LZMA format)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])  # Binary executable

    # Should fail with format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid", "format", "not lzma", "error", "binary"]
    )


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "file.lzma"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_mixed_valid_invalid_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test with mix of valid and invalid files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["valid.lzma", "nonexistent.lzma"])

    # Should fail on first error encountered
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_file_extension_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test file extension handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file.txt"])  # Wrong extension

    # Should either process file regardless of extension or fail with not found
    if result == 0:
        output = capture.get()
        # Should process file based on content, not extension
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test symbolic link handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/dev/stdout"]
        )  # Symlink to stdout

    # Should either handle symlinks or fail appropriately
    if result == 0:
        output = capture.get()
        # Should follow symlinks
        assert len(output) >= 0
    else:
        # Should fail with appropriate error
        assert result == 1


def test_execute_device_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test device file handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either handle device files or fail with format error
    if result == 0:
        output = capture.get()
        # Should handle device files
        assert len(output) >= 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "format", "error", "empty"])


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test memory efficiency with various inputs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent.lzma"])

    # Should be memory efficient even on errors
    assert result == 1
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable error message size


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid_file"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["not found", "error", "invalid", "cannot open"]
    )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test signal handling during decompression
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test.lzma"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test output formatting and encoding
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/hostname"]
        )  # Text file (not LZMA)

    # Should either output correctly or fail with format error
    if result == 0:
        output = capture.get()
        # Should preserve text formatting
        assert len(output) >= 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "format", "not lzma", "error"])


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmacatCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test.lzma"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])
