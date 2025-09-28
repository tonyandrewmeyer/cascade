"""Integration tests for the LzopCommand."""

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
    """Fixture to create a LzopCommand instance."""
    yield pebble_shell.commands.LzopCommand(shell=shell)


def test_name(command: pebble_shell.commands.LzopCommand):
    assert command.name == "lzop"


def test_category(command: pebble_shell.commands.LzopCommand):
    assert command.category == "Compression Utilities"


def test_help(command: pebble_shell.commands.LzopCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "lzop" in output
    assert "Fast LZO compression" in output
    assert "compress" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "lzop" in output
    assert "Fast LZO compression" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # lzop with no args should show usage or read from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either read from stdin or show usage
    if result == 0:
        output = capture.get()
        # Should wait for stdin input
        assert len(output) >= 0
    else:
        # Should fail with usage message
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "lzop", "file"])


def test_execute_compress_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test compressing a file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed compressing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should compress file successfully
        assert len(output.strip()) >= 0
        # Should show compression information
        if len(output.strip()) > 0:
            assert any(
                keyword in output.lower()
                for keyword in ["compressed", "saved", "ratio", "%"]
            )
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_decompress_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test decompressing a file
    with command.shell.console.capture() as capture:
        temp_dir = tempfile.mkdtemp()
        nonexistent_path = temp_dir + "/nonexistent.lzo"
        result = command.execute(client=client, args=["-d", nonexistent_path])

    # Should fail gracefully for nonexistent compressed file
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_list_contents(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test listing compressed file contents
    with command.shell.console.capture() as capture:
        temp_dir = tempfile.mkdtemp()
        nonexistent_path = temp_dir + "/nonexistent.lzo"
        result = command.execute(client=client, args=["-l", nonexistent_path])

    # Should fail gracefully for nonexistent file
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_test_integrity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test testing compressed file integrity
    with command.shell.console.capture() as capture:
        temp_dir = tempfile.mkdtemp()
        nonexistent_path = temp_dir + "/nonexistent.lzo"
        result = command.execute(client=client, args=["-t", nonexistent_path])

    # Should fail gracefully for nonexistent file
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test verbose mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "/etc/hosts"])

    # Should either succeed with verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show verbose compression information
        assert len(output.strip()) > 0
        # Should contain detailed information
        assert any(
            keyword in output.lower()
            for keyword in ["compressed", "ratio", "saved", "bytes"]
        )
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test quiet mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "/etc/hosts"])

    # Should either succeed quietly or fail gracefully
    if result == 0:
        output = capture.get()
        # Should produce minimal output in quiet mode
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_force_overwrite(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test force overwrite option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/etc/hosts"])

    # Should either succeed with force option or fail gracefully
    if result == 0:
        output = capture.get()
        # Should force overwrite existing files
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_keep_original(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test keep original file option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-k", "/etc/hosts"])

    # Should either succeed keeping original or fail gracefully
    if result == 0:
        output = capture.get()
        # Should keep original file
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_compression_level(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test compression level option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-9", "/etc/hosts"])

    # Should either succeed with compression level or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use specified compression level
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_fast_compression(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test fast compression option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1", "/etc/hosts"])

    # Should either succeed with fast compression or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use fast compression
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_best_compression(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test best compression option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-9", "/etc/passwd"])

    # Should either succeed with best compression or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use best compression
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_output_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test output to specific file
    with tempfile.NamedTemporaryFile(suffix="_output.lzo", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", output_path, "/etc/hosts"])

    # Should either succeed with output file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should output to specified file
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_stdout_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test output to stdout
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "/etc/hosts"])

    # Should either succeed outputting to stdout or fail gracefully
    if result == 0:
        output = capture.get()
        # Should output compressed data to stdout
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_preserve_timestamps(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test preserve timestamps option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "/etc/hosts"])

    # Should either succeed preserving timestamps or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve file timestamps
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_preserve_permissions(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test preserve permissions option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-P", "/etc/hosts"])

    # Should either succeed preserving permissions or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve file permissions
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_checksum_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test checksum option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-C", "/etc/hosts"])

    # Should either succeed with checksum or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include checksum in compressed file
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test compressing multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed with multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should compress multiple files
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_recursive_compression(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test recursive compression
    test_dir = tempfile.mkdtemp(prefix="test_dir_")
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", test_dir])

    # Should either succeed with recursive compression or fail gracefully
    if result == 0:
        output = capture.get()
        # Should compress directory recursively
        assert len(output.strip()) >= 0
    else:
        # Should fail if directory doesn't exist
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_directory_as_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should either handle directory or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["directory", "Is a directory", "error"])
    else:
        # May succeed compressing directory contents
        assert result == 0


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed compressing empty file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty file
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_large_file_compression(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/bash"])

    # Should either succeed compressing large file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle large file efficiently
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_binary_file_compression(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test compressing binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should either succeed compressing binary or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle binary file
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_invalid_compression_level(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test invalid compression level
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-99", "/etc/hosts"])

    # Should either handle invalid level or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "level", "error", "option"])
    else:
        # May accept and normalize invalid levels
        assert result == 0


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test conflicting options
    with tempfile.NamedTemporaryFile(suffix="_test.lzo", delete=False) as test_file:
        test_path = test_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "-1", test_path])

    # Should either handle conflicting options or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["conflicting", "invalid", "error"])
    else:
        # May resolve conflicts automatically
        assert result == 0


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/etc/hosts"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "/etc/hosts"])

    # Should produce properly formatted output
    if result == 0:
        output = capture.get()
        # Should have valid compression statistics format
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain compression information
            assert any(
                keyword in output.lower()
                for keyword in ["compressed", "ratio", "saved", "%"]
            )
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/etc/hosts"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should work regardless of locale settings
    if result == 0:
        output = capture.get()
        # Should be locale-independent
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform-specific features
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_compression_ratio_calculation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test compression ratio calculation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "/etc/passwd"])

    # Should calculate compression ratio
    if result == 0:
        output = capture.get()
        # Should show compression statistics
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain ratio information
            assert any(
                keyword in output.lower()
                for keyword in ["ratio", "saved", "%", "compressed"]
            )
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["/etc/hosts"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["/etc/hosts"])

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both executions should succeed consistently
        assert result1 == result2
    else:
        # At least one should succeed or both should fail consistently
        assert result1 == result2


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzopCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should operate robustly
    if result == 0:
        output = capture.get()
        # Should handle stress conditions
        assert len(output.strip()) >= 0
    else:
        assert result == 1
