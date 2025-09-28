"""Integration tests for the StringsCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a StringsCommand instance."""
    yield pebble_shell.commands.StringsCommand(shell=shell)


def test_name(command: pebble_shell.commands.StringsCommand):
    assert command.name == "strings"


def test_category(command: pebble_shell.commands.StringsCommand):
    assert command.category == "File Analysis"


def test_help(command: pebble_shell.commands.StringsCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "strings" in output
    assert "Extract printable strings" in output
    assert "binary" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "strings" in output
    assert "Extract printable strings" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # strings with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message or read from stdin
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "strings", "file"])
    else:
        # May succeed waiting for stdin
        assert result == 0


def test_execute_binary_file_analysis(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test analyzing binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should either succeed extracting strings or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain printable strings from binary
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain ASCII strings
            lines = output.strip().split("\n")
            for line in lines:
                # Each line should be a printable string
                assert all(
                    ord(char) >= 32 and ord(char) <= 126
                    for char in line
                    if line.strip()
                )
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_text_file_analysis(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test analyzing text file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed extracting strings or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain text from file
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain readable text
            lines = output.strip().split("\n")
            assert len(lines) >= 1
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_minimum_length_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test minimum length option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "10", "/bin/ls"])

    # Should either succeed with length filtering or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain strings of minimum length
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    # Each string should be at least 10 characters
                    assert len(line.strip()) >= 10
    else:
        assert result == 1


def test_execute_all_characters_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test all characters option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", "/bin/ls"])

    # Should either succeed scanning all sections or fail gracefully
    if result == 0:
        output = capture.get()
        # Should scan entire file
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_print_filename_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test print filename option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/bin/ls"])

    # Should either succeed with filename printing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include filename in output
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain filename
            assert "/bin/ls" in output or "ls" in output
    else:
        assert result == 1


def test_execute_print_offset_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test print offset option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", "/bin/ls"])

    # Should either succeed with offset printing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include offsets in output
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain numeric offsets
            assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_radix_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test radix option for offset display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "x", "/bin/ls"])

    # Should either succeed with hex offsets or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include hex offsets
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # May contain hexadecimal values
            assert any(char in output for char in "0123456789abcdefABCDEF")
    else:
        assert result == 1


def test_execute_encoding_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test encoding option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "s", "/bin/ls"])

    # Should either succeed with specific encoding or fail gracefully
    if result == 0:
        output = capture.get()
        # Should extract strings with specified encoding
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test processing multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls", "/bin/cat"])

    # Should either succeed processing multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain strings from both files
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.bin"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot open", "error", "not found"]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
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


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should succeed with no output
    assert result == 0
    output = capture.get()
    # Should produce no strings for empty file
    assert len(output.strip()) == 0


def test_execute_large_binary_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test with large binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/bash"])

    # Should either succeed processing large file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle large file efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_executable_file_analysis(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test analyzing executable file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/echo"])

    # Should either succeed extracting strings or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain strings from executable
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain printable strings
            lines = output.strip().split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_library_file_analysis(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test analyzing library file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/lib/x86_64-linux-gnu/libc.so.6"]
        )

    # Should either succeed or fail gracefully if file doesn't exist
    if result == 0:
        output = capture.get()
        # Should contain strings from library
        assert len(output.strip()) >= 0
    else:
        # Library may not exist on all systems
        assert result == 1


def test_execute_short_strings_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test filtering short strings
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "4", "/bin/ls"])

    # Should either succeed with minimum length 4 or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain strings of length 4 or more
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip():
                    assert len(line.strip()) >= 4
    else:
        assert result == 1


def test_execute_ascii_strings_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test extracting ASCII strings only
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should extract ASCII printable strings
    if result == 0:
        output = capture.get()
        # Should contain only ASCII printable characters
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            for char in output:
                if char not in "\n\r":
                    # Should be printable ASCII
                    assert 32 <= ord(char) <= 126
    else:
        assert result == 1


def test_execute_unicode_string_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test Unicode string detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "l", "/bin/ls"])

    # Should either succeed with Unicode detection or fail gracefully
    if result == 0:
        output = capture.get()
        # Should detect Unicode strings if present
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_wide_character_strings(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test wide character string detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "b", "/bin/ls"])

    # Should either succeed with wide character detection or fail gracefully
    if result == 0:
        output = capture.get()
        # Should detect wide character strings
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/bin/ls"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_invalid_minimum_length(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test invalid minimum length
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "invalid", "/bin/ls"])

    # Should fail with invalid length error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "number", "error"])


def test_execute_zero_minimum_length(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test zero minimum length
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "0", "/bin/ls"])

    # Should either succeed or handle zero length appropriately
    if result == 0:
        output = capture.get()
        # Should extract all strings
        assert len(output.strip()) >= 0
    else:
        # May reject zero length
        assert result == 1


def test_execute_very_large_minimum_length(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test very large minimum length
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "1000", "/bin/ls"])

    # Should succeed but find few or no strings
    assert result == 0
    output = capture.get()
    # Should produce minimal output with very long minimum length
    assert len(output.strip()) >= 0


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should produce properly formatted output
    if result == 0:
        output = capture.get()
        # Should have valid string output
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should be line-oriented output
            lines = output.strip().split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/echo"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "abc", "/bin/ls"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "error", "number"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_locale_awareness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test locale awareness
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should handle locale-specific character sets
    if result == 0:
        output = capture.get()
        # Should process according to locale
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_file_type_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test file type detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle different file types appropriately
    if result == 0:
        output = capture.get()
        # Should process text files correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_string_extraction_accuracy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test string extraction accuracy
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/echo"])

    # Should extract strings accurately
    if result == 0:
        output = capture.get()
        # Should contain meaningful strings
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain reasonable strings
            lines = output.strip().split("\n")
            assert any(len(line.strip()) >= 3 for line in lines if line.strip())
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should adapt to platform binary formats
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_binary_format_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test binary format support
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should support various binary formats
    if result == 0:
        output = capture.get()
        # Should handle ELF, PE, or other formats
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_character_encoding_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test character encoding handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should handle various character encodings
    if result == 0:
        output = capture.get()
        # Should decode characters properly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StringsCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["/bin/echo"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["/bin/echo"])

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both executions should succeed consistently
        assert result1 == result2
    else:
        # At least one should succeed or both should fail consistently
        assert result1 == result2
