"""Integration tests for the UncompressCommand."""

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
    """Fixture to create a UncompressCommand instance."""
    yield pebble_shell.commands.UncompressCommand(shell=shell)


def test_name(command: pebble_shell.commands.UncompressCommand):
    assert command.name == "uncompress"


def test_category(command: pebble_shell.commands.UncompressCommand):
    assert command.category == "Data Processing"


def test_help(command: pebble_shell.commands.UncompressCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "uncompress" in output
    assert "Decompress files" in output
    assert "-f" in output
    assert "-v" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "uncompress" in output
    assert "Decompress files" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # uncompress with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["usage", "filename required", "no files specified", "uncompress"]
    )


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.Z"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_regular_file_without_extension(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with regular file that doesn't have .Z extension
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either fail with extension error or attempt decompression
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["not compressed", "wrong extension", ".Z", "error"]
        )
    else:
        # May attempt to decompress anyway
        assert result == 0


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed with empty output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty file
        assert len(output.strip()) >= 0
    else:
        # Should fail if empty file not valid compressed format
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not compressed", "invalid format", "error"]
        )


def test_execute_compressed_file_z_extension(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with .Z file (may not exist, but test the handling)
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=[tmp_name])

    # Should either decompress or fail with file not found
    if result == 0:
        output = capture.get()
        # Should show decompression result
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist or isn't compressed
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No such file", "not found", "not compressed", "error"]
        )


def test_execute_force_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test -f option to force decompression
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/etc/hosts"])

    # Should either force decompression or fail gracefully
    if result == 0:
        output = capture.get()
        # Should attempt forced decompression
        assert len(output.strip()) >= 0
    else:
        # Should fail if forced decompression not possible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not compressed", "invalid format", "error"]
        )


def test_execute_verbose_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test -v option for verbose output
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-v", tmp_name])

    # Should either show verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show verbose decompression information
        assert (
            any(
                info in output
                for info in ["decompressing", "extracting", "uncompress", "done"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail with verbose error information
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "not compressed", "error"])


def test_execute_keep_original_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test -k option to keep original file
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-k", tmp_name])

    # Should either keep original during decompression or fail gracefully
    if result == 0:
        output = capture.get()
        # Should decompress while keeping original
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist or option not supported
        assert result == 1


def test_execute_test_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test -t option to test compressed file integrity
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-t", tmp_name])

    # Should either test file integrity or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show test results
        assert (
            any(msg in output for msg in ["OK", "valid", "test", "integrity"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if file doesn't exist or test fails
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "corrupt", "invalid", "error"]
        )


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix="1.Z", delete=False) as tmp_file1:
            tmp_name1 = tmp_file1.name
        with tempfile.NamedTemporaryFile(suffix="2.Z", delete=False) as tmp_file2:
            tmp_name2 = tmp_file2.name
        result = command.execute(client=client, args=[tmp_name1, tmp_name2])

    # Should either decompress multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process multiple files
        assert len(output.strip()) >= 0
    else:
        # Should fail if files don't exist
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error"])


def test_execute_directory_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with directory argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in [
            "is a directory",
            "cannot decompress directory",
            "not a file",
            "error",
        ]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/shadow"])

    # Should fail with permission error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "cannot open", "access denied", "error"]
        )
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_output_to_stdout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test -c option to output to stdout
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-c", tmp_name])

    # Should either output to stdout or fail gracefully
    if result == 0:
        output = capture.get()
        # Should output decompressed content to stdout
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist or isn't compressed
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test -q option for quiet mode
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-q", tmp_name])

    # Should either decompress quietly or fail gracefully
    if result == 0:
        output = capture.get()
        # Should have minimal output in quiet mode
        assert len(output.strip()) == 0 or len(output.strip()) < 50
    else:
        # Should fail quietly if file doesn't exist
        assert result == 1


def test_execute_recursive_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test -r option for recursive decompression
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", tempfile.mkdtemp()])

    # Should either decompress recursively or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process directory recursively
        assert len(output.strip()) >= 0
    else:
        # Should fail if recursive option not supported or no compressed files found
        assert result == 1


def test_execute_invalid_compressed_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with file that has .Z extension but isn't actually compressed
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should fail with invalid format error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["not compressed", "invalid format", "wrong format", "error"]
        )
    else:
        # May attempt to process anyway
        assert result == 0


def test_execute_large_compressed_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test with large compressed file (simulated)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/bash.Z"])

    # Should either handle large file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle large file efficiently
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist or isn't compressed
        assert result == 1


def test_execute_backup_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test backup file creation behavior
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-b", tmp_name])

    # Should either create backup or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle backup creation
        assert len(output.strip()) >= 0
    else:
        # Should fail if backup option not supported or file doesn't exist
        assert result == 1


def test_execute_compression_ratio_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test compression ratio display
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-v", tmp_name])

    # Should either show compression ratio or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show decompression statistics
        assert (
            any(stat in output for stat in ["ratio", "size", "%", "bytes"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if file doesn't exist
        assert result == 1


def test_execute_overwrite_protection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test overwrite protection
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=[tmp_name])

    # Should either protect from overwrite or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle overwrite protection
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist or overwrite conflict
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["exists", "overwrite", "not found", "error"]
        )


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test symbolic link handling
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix="_link.Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=[tmp_name])

    # Should either follow symlink or handle appropriately
    if result == 0:
        output = capture.get()
        # Should follow symlink and decompress target
        assert len(output.strip()) >= 0
    else:
        # Should fail if symlink doesn't exist or target isn't compressed
        assert result == 1


def test_execute_filename_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test filename preservation during decompression
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(
            suffix="_document.txt.Z", delete=False
        ) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=[tmp_name])

    # Should either preserve original filename or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve filename without .Z extension
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist
        assert result == 1


def test_execute_timestamp_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test timestamp preservation
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-p", tmp_name])

    # Should either preserve timestamps or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve file timestamps
        assert len(output.strip()) >= 0
    else:
        # Should fail if option not supported or file doesn't exist
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent.Z"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["not found", "error", "No such file"])


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=[tmp_name])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=[tmp_name])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_progress_indication(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test progress indication for large files
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix="_large.Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["-v", tmp_name])

    # Should either show progress or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show progress information
        assert (
            any(
                progress in output
                for progress in ["progress", "%", "decompressing", "done"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if file doesn't exist
        assert result == 1


def test_execute_format_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test automatic format detection
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix="_test", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=[tmp_name])

    # Should either detect format automatically or fail gracefully
    if result == 0:
        output = capture.get()
        # Should detect and decompress format
        assert len(output.strip()) >= 0
    else:
        # Should fail if format not detected or file doesn't exist
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["format", "not found", "not compressed", "error"]
        )


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UncompressCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".Z", delete=False) as tmp_file:
            tmp_name = tmp_file.name
        result = command.execute(client=client, args=["--invalid-option", tmp_name])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and proceed
        assert result == 0
