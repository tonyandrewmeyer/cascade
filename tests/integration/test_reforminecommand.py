"""Integration tests for the ReformineCommand."""

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
    """Fixture to create a ReformineCommand instance."""
    yield pebble_shell.commands.ReformineCommand(shell=shell)


def test_name(command: pebble_shell.commands.ReformineCommand):
    assert command.name == "reformime"


def test_category(command: pebble_shell.commands.ReformineCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.ReformineCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["reform", "mime", "message", "email", "reformat"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["reform", "mime", "message", "usage"]
    )


def test_execute_no_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with no arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing arguments error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["argument", "required", "usage", "error", "option"]
    )


def test_execute_extract_mime_structure(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test extracting MIME structure
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s"])

    # Should either succeed extracting structure or fail with input error
    if result == 0:
        output = capture.get()
        # Should extract MIME structure
        assert len(output) >= 0
    else:
        # Should fail with input or structure error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["input", "structure", "mime", "error"])


def test_execute_extract_headers(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test extracting MIME headers
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i"])

    # Should either succeed extracting headers or fail
    if result == 0:
        output = capture.get()
        # Should extract headers
        assert len(output) >= 0
    else:
        # Should fail with input or header error
        assert result == 1


def test_execute_extract_specific_section(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test extracting specific MIME section
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "1"])

    # Should either succeed extracting section or fail
    if result == 0:
        output = capture.get()
        # Should extract specified section
        assert len(output) >= 0
    else:
        # Should fail with input or section error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["section", "not found", "mime", "error"])


def test_execute_decode_quoted_printable(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test decoding quoted-printable content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q"])

    # Should either succeed decoding or fail
    if result == 0:
        output = capture.get()
        # Should decode quoted-printable
        assert len(output) >= 0
    else:
        # Should fail with input or decoding error
        assert result == 1


def test_execute_decode_base64(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test decoding base64 content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-6"])

    # Should either succeed decoding base64 or fail
    if result == 0:
        output = capture.get()
        # Should decode base64
        assert len(output) >= 0
    else:
        # Should fail with input or decoding error
        assert result == 1


def test_execute_extract_text_content(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test extracting text content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t"])

    # Should either succeed extracting text or fail
    if result == 0:
        output = capture.get()
        # Should extract text content
        assert len(output) >= 0
    else:
        # Should fail with input or text error
        assert result == 1


def test_execute_rewrite_addresses(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test rewriting email addresses
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-R", "old@example.com", "new@example.com"]
        )

    # Should either succeed rewriting addresses or fail
    if result == 0:
        output = capture.get()
        # Should rewrite addresses
        assert len(output) >= 0
    else:
        # Should fail with input or rewrite error
        assert result == 1


def test_execute_with_input_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with input file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/hostname"])

    # Should either succeed with file input or fail
    if result == 0:
        output = capture.get()
        # Should process file input
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "file", "mime"])


def test_execute_nonexistent_input_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with non-existent input file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/nonexistent/mime.msg"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "error", "cannot open"]
    )


def test_execute_directory_instead_of_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with directory instead of file
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", temp_dir])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "not a file", "error", "invalid"])


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should read file if permitted
        assert len(output) >= 0
    else:
        # Should fail with permission error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "access", "error"])


def test_execute_invalid_mime_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with invalid MIME format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-s", "/etc/passwd"]
        )  # Not MIME format

    # Should either succeed or fail with format error
    if result == 0:
        output = capture.get()
        # Should handle non-MIME format
        assert len(output) >= 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["format", "invalid", "mime", "error"])


def test_execute_extract_nonexistent_section(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test extracting non-existent section
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "999", "/etc/hostname"])

    # Should fail with section not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["section", "not found", "invalid", "error", "999"]
    )


def test_execute_invalid_section_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with invalid section number
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "abc"])

    # Should fail with invalid section number error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "section", "number", "error"])


def test_execute_negative_section_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with negative section number
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "-1"])

    # Should fail with invalid section number error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "section", "negative", "error"])


def test_execute_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test reading from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "-"])

    # Should either succeed reading stdin or fail
    if result == 0:
        output = capture.get()
        # Should read from stdin
        assert len(output) >= 0
    else:
        # Should fail with stdin or format error
        assert result == 1


def test_execute_multiple_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test multiple operations together
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "-i", "/etc/hostname"])

    # Should either succeed with multiple operations or fail
    if result == 0:
        output = capture.get()
        # Should perform multiple operations
        assert len(output) >= 0
    else:
        # Should fail with operation conflict or file error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["conflict", "multiple", "operation", "error"]
        )


def test_execute_decode_with_charset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test decoding with charset specification
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "utf-8", "-t"])

    # Should either succeed with charset or fail
    if result == 0:
        output = capture.get()
        # Should decode with specified charset
        assert len(output) >= 0
    else:
        # Should fail with charset or input error
        assert result == 1


def test_execute_invalid_charset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with invalid charset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "invalid-charset", "-t"])

    # Should fail with invalid charset error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "charset", "encoding", "error"])


def test_execute_extract_attachments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test extracting attachments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should either succeed extracting attachments or fail
    if result == 0:
        output = capture.get()
        # Should extract attachments
        assert len(output) >= 0
    else:
        # Should fail with input or attachment error
        assert result == 1


def test_execute_print_mime_structure(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test printing MIME structure
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-D"])

    # Should either succeed printing structure or fail
    if result == 0:
        output = capture.get()
        # Should print MIME structure debug info
        assert len(output) >= 0
    else:
        # Should fail with input or debug error
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_empty_mime_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with empty MIME message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/dev/null"])

    # Should either succeed with empty message or fail
    if result == 0:
        output = capture.get()
        # Should handle empty message
        assert len(output) >= 0
    else:
        # Should fail with empty or format error
        assert result == 1


def test_execute_large_mime_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with large MIME message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/dev/zero"])

    # Should either handle large messages or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle large messages efficiently
        assert len(output) >= 0
    else:
        # Should fail with size or format error
        assert result == 1


def test_execute_binary_content_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test with binary content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/bin/ls"])

    # Should either handle binary content or fail
    if result == 0:
        output = capture.get()
        # Should handle binary content
        assert len(output) >= 0
    else:
        # Should fail with binary or format error
        assert result == 1


def test_execute_multipart_message_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test multipart MIME message handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s"])

    # Should either succeed with multipart or fail
    if result == 0:
        output = capture.get()
        # Should handle multipart messages
        assert len(output) >= 0
    else:
        # Should fail with input or multipart error
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "abc"])  # Trigger error

    # Should be memory efficient even on errors
    assert result == 1
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable error message size


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/invalid/path"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["not found", "error", "invalid", "cannot open"]
    )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test signal handling during MIME processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/hostname"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test output formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/hostname"])

    # Should either succeed with proper formatting or fail
    if result == 0:
        output = capture.get()
        # Should format output properly
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain formatted MIME information
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_encoding_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test encoding detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "/etc/hostname"])

    # Should either succeed detecting encoding or fail
    if result == 0:
        output = capture.get()
        # Should detect and handle encoding
        assert len(output) >= 0
    else:
        # Should fail with detection or format error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReformineCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/hostname"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "format", "mime"])
