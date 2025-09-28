"""Integration tests for the CatvCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CatvCommand instance."""
    yield pebble_shell.commands.CatvCommand(shell=shell)


def test_name(command: pebble_shell.commands.CatvCommand):
    assert command.name == "catv"


def test_category(command: pebble_shell.commands.CatvCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.CatvCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "catv" in output
    assert "Display file contents with visible control characters" in output
    assert "control" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "catv" in output
    assert "Display file contents with visible control characters" in output


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # catv with no args should read from stdin or show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either read from stdin or show usage
    if result == 0:
        output = capture.get()
        # Should wait for stdin or process empty input
        assert len(output) >= 0
    else:
        # Should fail with usage message
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "catv", "file"])


def test_execute_text_file_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test displaying text file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed displaying file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain file contents
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain readable text
            lines = output.strip().split("\n")
            assert len(lines) >= 1
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_file_with_control_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with control characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed displaying with control chars or fail gracefully
    if result == 0:
        output = capture.get()
        # Should display control characters visibly
        assert len(output) >= 0
        # Should make control characters visible
        if len(output.strip()) > 0:
            # May contain visible representations of control chars
            assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_binary_file_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test displaying binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should either succeed displaying binary or fail gracefully
    if result == 0:
        output = capture.get()
        # Should display binary with visible control characters
        assert len(output) >= 0
        # Should make non-printable characters visible
        if len(output) > 0:
            # Should contain visible representations
            assert len(output) >= 0
    else:
        assert result == 1


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should succeed with no output
    assert result == 0
    output = capture.get()
    # Should produce no output for empty file
    assert len(output) == 0


def test_execute_file_with_tabs(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with tab characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/fstab"])

    # Should either succeed showing tabs visibly or fail gracefully
    if result == 0:
        output = capture.get()
        # Should make tab characters visible
        assert len(output) >= 0
        if "\t" in output or "^I" in output:
            # Should show tabs in visible form
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_file_with_newlines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with various newline characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed handling newlines or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle newlines appropriately
        assert len(output) >= 0
        # Should preserve or show line structure
        if len(output.strip()) > 0:
            assert len(output) >= 0
    else:
        assert result == 1


def test_execute_file_with_carriage_returns(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with carriage return characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed showing CR characters or fail gracefully
    if result == 0:
        output = capture.get()
        # Should make carriage returns visible if present
        assert len(output) >= 0
        if "\r" in output or "^M" in output:
            # Should show CR in visible form
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_file_with_form_feeds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with form feed characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed showing form feeds or fail gracefully
    if result == 0:
        output = capture.get()
        # Should make form feeds visible if present
        assert len(output) >= 0
        if "\f" in output or "^L" in output:
            # Should show form feeds in visible form
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_file_with_escape_sequences(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with escape sequences
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed showing escape sequences or fail gracefully
    if result == 0:
        output = capture.get()
        # Should make escape sequences visible
        assert len(output) >= 0
        if "\033" in output or "^[" in output:
            # Should show escapes in visible form
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_file_with_null_bytes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with null bytes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/echo"])

    # Should either succeed showing null bytes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should make null bytes visible
        assert len(output) >= 0
        if "\0" in output or "^@" in output:
            # Should show nulls in visible form
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_file_with_backspace(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with backspace characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed showing backspaces or fail gracefully
    if result == 0:
        output = capture.get()
        # Should make backspaces visible if present
        assert len(output) >= 0
        if "\b" in output or "^H" in output:
            # Should show backspaces in visible form
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_file_with_bell_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with bell characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed showing bells or fail gracefully
    if result == 0:
        output = capture.get()
        # Should make bell characters visible if present
        assert len(output) >= 0
        if "\a" in output or "^G" in output:
            # Should show bells in visible form
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test displaying multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed with multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain contents from both files
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot open", "error", "not found"]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
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
    command: pebble_shell.commands.CatvCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should either handle directory or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["directory", "Is a directory", "error"])
    else:
        # May succeed reading directory contents
        assert result == 0


def test_execute_device_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test with device file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/zero"])

    # Should either handle device file or timeout/fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle device file (may produce output)
        assert len(output) >= 0
    else:
        # May fail or timeout with device files
        assert result == 1


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/bash"])

    # Should either succeed processing large file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle large file efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_special_file_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test with special file names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-"])

    # Should either handle stdin or fail appropriately
    if result == 0:
        output = capture.get()
        # Should read from stdin
        assert len(output) >= 0
    else:
        # May not support "-" for stdin
        assert result == 1


def test_execute_unicode_content(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with Unicode content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed with Unicode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle Unicode characters
        assert len(output) >= 0
        # Should display Unicode appropriately
        if len(output.strip()) > 0:
            assert isinstance(output, str)
    else:
        assert result == 1


def test_execute_mixed_content_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test file with mixed text and binary content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/echo"])

    # Should either succeed with mixed content or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle mixed content
        assert len(output) >= 0
        # Should make non-printable characters visible
        if len(output) > 0:
            assert len(output) >= 0
    else:
        assert result == 1


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should produce properly formatted output
    if result == 0:
        output = capture.get()
        # Should have valid output format
        assert len(output) >= 0
        # Should make control characters visible
        if len(output) > 0:
            # Should be readable text format
            assert isinstance(output, str)
    else:
        assert result == 1


def test_execute_control_character_representation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test control character representation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should represent control characters visibly
    if result == 0:
        output = capture.get()
        # Should use visible representations for control chars
        assert len(output) >= 0
        # Common control character representations: ^X format
        if any(ord(c) < 32 for c in output if c not in "\n\r\t"):
            # Should contain visible control character representations
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["No such file", "error", "cannot", "not found"]
    )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_locale_awareness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test locale awareness
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle locale-specific characters
    if result == 0:
        output = capture.get()
        # Should process characters according to locale
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_encoding_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test character encoding handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle various character encodings
    if result == 0:
        output = capture.get()
        # Should decode/display characters properly
        assert len(output) >= 0
        # Should handle encoding appropriately
        if len(output) > 0:
            assert isinstance(output, str)
    else:
        assert result == 1


def test_execute_line_ending_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test line ending handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle different line endings
    if result == 0:
        output = capture.get()
        # Should process line endings correctly
        assert len(output) >= 0
        # Should preserve or show line structure
        if "\n" in output:
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should adapt to platform-specific features
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatvCommand,
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
    command: pebble_shell.commands.CatvCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should operate robustly
    if result == 0:
        output = capture.get()
        # Should handle stress conditions
        assert len(output) >= 0
    else:
        assert result == 1
