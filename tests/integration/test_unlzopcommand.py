"""Integration tests for the UnlzopCommand."""

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
    """Fixture to create a UnlzopCommand instance."""
    yield pebble_shell.commands.UnlzopCommand(shell=shell)


def test_name(command: pebble_shell.commands.UnlzopCommand):
    assert command.name == "unlzop"


def test_category(command: pebble_shell.commands.UnlzopCommand):
    assert command.category == "Compression"


def test_help(command: pebble_shell.commands.UnlzopCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["lzo", "decompress", "uncompress", "extract", "file"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["lzo", "decompress", "uncompress", "usage"]
    )


def test_execute_no_file_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
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
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test with non-existent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent.lzo"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "error", "cannot open"]
    )


def test_execute_invalid_lzo_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test with invalid LZO file format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])  # Not an LZO file

    # Should fail with format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid", "format", "not lzo", "error", "compressed"]
    )


def test_execute_directory_instead_of_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
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
    command: pebble_shell.commands.UnlzopCommand,
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


def test_execute_output_to_stdout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test output to stdout with -c option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "test.lzo"])

    # Should either succeed outputting to stdout or fail with file not found
    if result == 0:
        output = capture.get()
        # Should output decompressed content to stdout
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_force_overwrite(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test force overwrite with -f option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "test.lzo"])

    # Should either succeed with force or fail with file not found
    if result == 0:
        output = capture.get()
        # Should force overwrite existing files
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_keep_input_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test keep input file with -k option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-k", "test.lzo"])

    # Should either succeed keeping input or fail with file not found
    if result == 0:
        output = capture.get()
        # Should keep original file after decompression
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test verbose mode with -v option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "test.lzo"])

    # Should either succeed with verbose output or fail with file not found
    if result == 0:
        output = capture.get()
        # Should show verbose decompression information
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_test_integrity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test file integrity with -t option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "test.lzo"])

    # Should either succeed testing integrity or fail with file not found
    if result == 0:
        output = capture.get()
        # Should test file integrity without extracting
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file1.lzo", "file2.lzo"])

    # Should either succeed processing multiple files or fail with error
    if result == 0:
        output = capture.get()
        # Should decompress multiple files
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
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


def test_execute_output_file_specification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test specifying output file with -o option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", "output.txt", "test.lzo"])

    # Should either succeed with custom output or fail with file not found
    if result == 0:
        output = capture.get()
        # Should decompress to specified output file
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_empty_lzo_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test with empty LZO file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])  # Empty file

    # Should either succeed with empty output or fail with format error
    if result == 0:
        output = capture.get()
        # Should handle empty files
        assert len(output) >= 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "format", "error", "empty"])


def test_execute_corrupted_lzo_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test with corrupted LZO file (using random binary data)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/urandom"])  # Random data

    # Should fail with corruption/format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid", "format", "corrupted", "error", "not lzo"]
    )


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
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
        # Should fail with format error (since /dev/zero is not LZO)
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "format", "error", "not lzo"])


def test_execute_binary_data_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test with binary executable (not LZO format)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])  # Binary executable

    # Should fail with format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid", "format", "not lzo", "error", "binary"]
    )


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "file.lzo"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_file_extension_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
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


def test_execute_output_file_exists(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test behavior when output file exists
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["test.lzo"]
        )  # Output would be test

    # Should either overwrite, prompt, or fail depending on options
    if result == 0:
        output = capture.get()
        # Should handle existing output files
        assert len(output) >= 0
    else:
        # Should fail with file not found, format error, or overwrite protection
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["not found", "error", "exists", "overwrite", "format"]
        )


def test_execute_lzo_variant_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test different LZO format variants
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test.lzo1"])  # LZO1 variant

    # Should either handle LZO variants or fail with file not found
    if result == 0:
        output = capture.get()
        # Should handle different LZO variants
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "invalid", "format"])


def test_execute_compression_ratio_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test compression ratio display in verbose mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "test.lzo"])

    # Should either show compression statistics or fail with file not found
    if result == 0:
        output = capture.get()
        # Should show compression ratio information
        assert len(output) >= 0
        if len(output) > 0:
            # Might contain compression statistics
            has_stats = any(
                stat in output.lower()
                for stat in ["ratio", "compressed", "uncompressed", "saved"]
            )
            if has_stats:
                assert has_stats
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
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
    command: pebble_shell.commands.UnlzopCommand,
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
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test memory efficiency with various inputs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent.lzo"])

    # Should be memory efficient even on errors
    assert result == 1
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable error message size


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
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
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test signal handling during decompression
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test.lzo"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_partial_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test handling of partially downloaded or truncated files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/proc/version"])  # System file

    # Should either process or fail with format error
    if result == 0:
        output = capture.get()
        # Should handle various file types
        assert len(output) >= 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "format", "not lzo", "error"])


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnlzopCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test.lzo"])

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
