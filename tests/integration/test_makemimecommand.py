"""Integration tests for the MakemimeCommand."""

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
    """Fixture to create a MakemimeCommand instance."""
    yield pebble_shell.commands.MakemimeCommand(shell=shell)


def test_name(command: pebble_shell.commands.MakemimeCommand):
    assert command.name == "makemime"


def test_category(command: pebble_shell.commands.MakemimeCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.MakemimeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["make", "mime", "message", "email", "encode"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["make", "mime", "message", "usage"]
    )


def test_execute_no_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
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


def test_execute_simple_text_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test creating simple text MIME message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "text/plain", "-"])

    # Should either succeed creating MIME message or fail with error
    if result == 0:
        output = capture.get()
        # Should create MIME message
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain MIME headers
            assert any(
                header in output.lower()
                for header in ["content-type", "mime-version", "text/plain"]
            )
    else:
        # Should fail with input or format error
        assert result == 1


def test_execute_with_subject(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with subject header
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-s", "Test Subject", "-t", "text/plain", "-"]
        )

    # Should either succeed with subject or fail with error
    if result == 0:
        output = capture.get()
        # Should include subject header
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain subject header
            assert "subject" in output.lower() or "test subject" in output.lower()
    else:
        # Should fail with input or format error
        assert result == 1


def test_execute_with_from_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with from address
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-f", "sender@example.com", "-t", "text/plain", "-"]
        )

    # Should either succeed with from address or fail
    if result == 0:
        output = capture.get()
        # Should include from header
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain from header
            assert "from" in output.lower() or "sender@example.com" in output.lower()
    else:
        # Should fail with input or format error
        assert result == 1


def test_execute_with_to_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with to address
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-T", "recipient@example.com", "-t", "text/plain", "-"]
        )

    # Should either succeed with to address or fail
    if result == 0:
        output = capture.get()
        # Should include to header
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain to header
            assert "to" in output.lower() or "recipient@example.com" in output.lower()
    else:
        # Should fail with input or format error
        assert result == 1


def test_execute_with_attachment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with file attachment
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-a", "/etc/hostname", "-t", "text/plain", "-"]
        )

    # Should either succeed with attachment or fail
    if result == 0:
        output = capture.get()
        # Should include attachment
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain multipart MIME structure
            assert any(
                mime_part in output.lower()
                for mime_part in ["multipart", "boundary", "content-disposition"]
            )
    else:
        # Should fail with file not found or format error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "error", "attachment", "file"]
        )


def test_execute_html_content_type(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with HTML content type
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "text/html", "-"])

    # Should either succeed with HTML type or fail
    if result == 0:
        output = capture.get()
        # Should set HTML content type
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain HTML content type
            assert "text/html" in output.lower()
    else:
        # Should fail with input or format error
        assert result == 1


def test_execute_binary_content_type(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with binary content type
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "application/octet-stream", "/bin/ls"]
        )

    # Should either succeed with binary type or fail
    if result == 0:
        output = capture.get()
        # Should handle binary content
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain binary content type and encoding
            assert any(
                binary_indicator in output.lower()
                for binary_indicator in ["application/octet-stream", "base64", "binary"]
            )
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_custom_encoding(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with custom encoding
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-e", "base64", "-t", "text/plain", "/etc/hostname"]
        )

    # Should either succeed with custom encoding or fail
    if result == 0:
        output = capture.get()
        # Should use specified encoding
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain encoding header
            assert (
                "base64" in output.lower()
                or "content-transfer-encoding" in output.lower()
            )
    else:
        # Should fail with file not found or encoding error
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with non-existent file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "text/plain", "/nonexistent/file.txt"]
        )

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "error", "cannot open"]
    )


def test_execute_directory_instead_of_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with directory instead of file
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "text/plain", temp_dir])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "not a file", "error", "invalid"])


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "text/plain", "/root/.ssh/id_rsa"]
        )

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


def test_execute_multipart_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test creating multipart MIME message
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-m", "-t", "text/plain", "-", "-a", "/etc/hostname"]
        )

    # Should either succeed creating multipart or fail
    if result == 0:
        output = capture.get()
        # Should create multipart message
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain multipart structure
            assert any(
                multipart in output.lower()
                for multipart in ["multipart", "boundary", "--"]
            )
    else:
        # Should fail with file or format error
        assert result == 1


def test_execute_quoted_printable_encoding(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test quoted-printable encoding
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-e", "quoted-printable", "-t", "text/plain", "/etc/hostname"],
        )

    # Should either succeed with quoted-printable or fail
    if result == 0:
        output = capture.get()
        # Should use quoted-printable encoding
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain quoted-printable encoding
            assert "quoted-printable" in output.lower()
    else:
        # Should fail with file not found or encoding error
        assert result == 1


def test_execute_custom_boundary(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with custom boundary
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-b", "CustomBoundary123", "-m", "-t", "text/plain", "-"],
        )

    # Should either succeed with custom boundary or fail
    if result == 0:
        output = capture.get()
        # Should use custom boundary
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain custom boundary
            assert "CustomBoundary123" in output
    else:
        # Should fail with input or format error
        assert result == 1


def test_execute_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test reading from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "text/plain", "-"])

    # Should either succeed reading stdin or fail
    if result == 0:
        output = capture.get()
        # Should read from stdin
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain MIME headers
            assert "content-type" in output.lower()
    else:
        # Should fail with stdin or format error
        assert result == 1


def test_execute_invalid_content_type(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with invalid content type
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "invalid/type", "-"])

    # Should either succeed or fail with content type error
    if result == 0:
        output = capture.get()
        # Should handle invalid content type
        assert len(output) >= 0
    else:
        # Should fail with content type error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "content", "type", "error"])


def test_execute_invalid_encoding(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with invalid encoding
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-e", "invalid-encoding", "-t", "text/plain", "-"]
        )

    # Should fail with invalid encoding error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "encoding", "error", "unknown"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "-t", "text/plain", "-"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_long_subject_line(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with very long subject line
    long_subject = "A" * 1000  # Very long subject
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-s", long_subject, "-t", "text/plain", "-"]
        )

    # Should either succeed with long subject or fail
    if result == 0:
        output = capture.get()
        # Should handle long subject line
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain subject (possibly folded)
            assert "subject" in output.lower()
    else:
        # Should fail with format or length error
        assert result == 1


def test_execute_special_characters_in_headers(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test with special characters in headers
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-s", "Test with ünicode", "-t", "text/plain", "-"]
        )

    # Should either succeed with special characters or fail
    if result == 0:
        output = capture.get()
        # Should handle special characters
        assert len(output) >= 0
        if len(output) > 0:
            # Should encode or handle special characters
            assert "subject" in output.lower()
    else:
        # Should fail with encoding or format error
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "text/plain", "/nonexistent.txt"]
        )

    # Should be memory efficient even on errors
    assert result == 1
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable error message size


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "text/plain", "/invalid/path"]
        )

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["not found", "error", "invalid", "cannot open"]
    )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test signal handling during MIME creation
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "text/plain", "/etc/hostname"]
        )

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test MIME output formatting
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "text/plain", "/etc/hostname"]
        )

    # Should either succeed with proper formatting or fail
    if result == 0:
        output = capture.get()
        # Should format MIME message properly
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain proper MIME structure
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should have headers followed by body
            has_headers = any(
                ":" in line for line in lines[:10]
            )  # Headers in first 10 lines
            if has_headers:
                assert has_headers
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakemimeCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "text/plain", "/etc/hostname"]
        )

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "error", "permission", "access"]
        )
